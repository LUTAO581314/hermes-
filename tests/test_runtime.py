import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.hermes.capabilities import collect_capabilities
from src.hermes.cli import build_parser, run
from src.hermes.config import load_settings
from src.hermes.db import database_status
from src.hermes.document_pipeline import generate_document_memory_candidates, index_document_artifacts, register_document_artifacts, run_document_ingest
from src.hermes.adapters.everos import build_search_payload, status as everos_status
from src.hermes.adapters.funasr import build_server_command as build_funasr_server_command, build_transcription_payload as build_funasr_transcription_payload, status as funasr_status
from src.hermes.adapters.mineru import build_parse_command as build_mineru_parse_command, status as mineru_status
from src.hermes.adapters.mirofish import build_dev_command, status as mirofish_status
from src.hermes.adapters.searxng import build_docker_command as build_searxng_docker_command, build_search_payload as build_searxng_search_payload, status as searxng_status
from src.hermes.adapters.sonic import build_docker_command as build_sonic_docker_command, build_query_payload as build_sonic_query_payload, status as sonic_status
from src.hermes.adapters.trendradar import build_mcp_command, status as trendradar_status
from src.hermes.license import load_license, sign_license_payload
from src.hermes.model_gateway import build_chat_payload, complete_chat
from src.hermes.platform import HEARTBEAT_PROTOCOL_VERSION, build_platform_heartbeat
from src.hermes.runtime_readiness import collect_runtime_readiness
from src.hermes.storage import (
    create_document_ingest,
    create_job,
    list_audit_events,
    list_document_artifacts,
    list_document_index_runs,
    list_document_ingest_runs,
    list_document_ingests,
    list_document_memory_candidates,
    list_jobs,
    write_obsidian_report,
)


class RuntimeFoundationTests(unittest.TestCase):
    def test_load_settings_defaults(self):
        settings = load_settings()
        self.assertEqual(settings.product_name, "bairui Agent OS")
        self.assertEqual(settings.brand_key, "bairui")
        self.assertEqual(settings.trademark_name, "bairui")
        self.assertEqual(settings.logo_text, "bairui")
        self.assertEqual(settings.port, 8787)

    def test_missing_license_reports_missing_config(self):
        state = load_license(Path("__missing_license__.json"))
        self.assertEqual(state.status, "missing_config")

    def test_license_file_is_parsed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "license.json"
            path.write_text(json.dumps({"license_id": "lic_1", "organization_id": "org_1", "plan": "starter"}), encoding="utf-8")
            state = load_license(path)
            self.assertEqual(state.status, "unsigned")
            self.assertEqual(state.license_id, "lic_1")

    def test_signed_license_is_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "license.json"
            payload = {"license_id": "lic_1", "organization_id": "org_1", "plan": "starter", "features": ["jobs"]}
            payload["signature"] = sign_license_payload(payload, "secret")
            path.write_text(json.dumps(payload), encoding="utf-8")
            state = load_license(path, "secret")
            self.assertEqual(state.status, "valid")
            self.assertEqual(state.features, ("jobs",))

    def test_bad_license_signature_is_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "license.json"
            payload = {"license_id": "lic_1", "organization_id": "org_1", "plan": "starter", "signature": "bad"}
            path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(load_license(path, "secret").status, "invalid")

    def test_capabilities_include_vendor_runtimes(self):
        settings = load_settings()
        names = {cap["name"] for cap in collect_capabilities(settings)}
        self.assertIn("everos_memory", names)
        self.assertIn("trendradar_intelligence", names)
        self.assertIn("mirofish_simulation", names)
        self.assertIn("jobs_api", names)
        self.assertIn("model_gateway", names)

    def test_create_job_writes_job_and_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            job = create_job(data_dir, title="First job", prompt="Summarize this", route="research")
            self.assertEqual(job.status, "queued")
            self.assertEqual(len(list_jobs(data_dir)), 1)
            audit = list_audit_events(data_dir)
            self.assertEqual(audit[0]["action"], "job.created")

    def test_create_document_ingest_writes_plan_and_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            ingest = create_document_ingest(
                data_dir,
                title="Contract",
                input_path="contract.pdf",
                output_dir="out",
                parser_command=("mineru", "-p", "contract.pdf", "-o", "out"),
            )
            self.assertEqual(ingest.status, "planned")
            self.assertEqual(ingest.pipeline["parse"], "planned")
            self.assertEqual(ingest.pipeline["sonic_index"], "pending")
            records = list_document_ingests(data_dir)
            self.assertEqual(records[0]["parser"], "mineru")
            self.assertEqual(records[0]["title"], "Contract")
            audit = list_audit_events(data_dir)
            self.assertEqual(audit[0]["action"], "document.ingest_planned")

    def test_run_document_ingest_records_successful_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            ingest = create_document_ingest(
                data_dir,
                title="Executable plan",
                input_path="sample.pdf",
                output_dir="out",
                parser_command=("python", "-c", "print('mineru ok')"),
            )
            result = run_document_ingest(data_dir, ingest.id, timeout_seconds=10)
            self.assertEqual(result.status, "completed")
            self.assertIsNotNone(result.run)
            runs = list_document_ingest_runs(data_dir)
            self.assertEqual(runs[0]["ingest_id"], ingest.id)
            self.assertEqual(runs[0]["exit_code"], 0)
            self.assertIn("mineru ok", runs[0]["stdout"])
            self.assertEqual(list_audit_events(data_dir)[1]["action"], "document.ingest_run_finished")

    def test_run_document_ingest_records_missing_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            ingest = create_document_ingest(
                data_dir,
                title="Missing command",
                input_path="sample.pdf",
                output_dir="out",
                parser_command=("__missing_mineru_binary__", "-p", "sample.pdf"),
            )
            result = run_document_ingest(data_dir, ingest.id, timeout_seconds=10)
            self.assertEqual(result.status, "failed")
            runs = list_document_ingest_runs(data_dir)
            self.assertIsNone(runs[0]["exit_code"])
            self.assertIn("__missing_mineru_binary__", runs[0]["error"])

    def test_register_document_artifacts_records_real_output_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            nested_dir = output_dir / "images"
            nested_dir.mkdir(parents=True)
            markdown = output_dir / "sample.md"
            metadata = output_dir / "sample.json"
            image = nested_dir / "page-1.png"
            markdown.write_text("# Sample\n\nParsed text", encoding="utf-8")
            metadata.write_text('{"pages": 1}', encoding="utf-8")
            image.write_bytes(b"\x89PNG\r\n\x1a\n")
            ingest = create_document_ingest(
                data_dir,
                title="Artifact plan",
                input_path="sample.pdf",
                output_dir=str(output_dir),
                parser_command=("mineru", "-p", "sample.pdf", "-o", str(output_dir)),
            )
            result = register_document_artifacts(data_dir, ingest.id)
            records = list_document_artifacts(data_dir)
            audit = list_audit_events(data_dir)
        self.assertEqual(result.status, "completed")
        self.assertEqual(len(result.artifacts), 3)
        self.assertEqual(len(records), 3)
        types = {record["relative_path"]: record["artifact_type"] for record in records}
        self.assertEqual(types["sample.md"], "markdown")
        self.assertEqual(types["sample.json"], "json")
        self.assertEqual(types["images\\page-1.png"] if "images\\page-1.png" in types else types["images/page-1.png"], "image")
        self.assertTrue(all(record["sha256"] for record in records))
        self.assertTrue(all(record["size_bytes"] > 0 for record in records))
        self.assertEqual(audit[1]["action"], "document.artifacts_registered")

    def test_register_document_artifacts_reports_missing_output_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            ingest = create_document_ingest(
                data_dir,
                title="Missing output",
                input_path="sample.pdf",
                output_dir=str(Path(tmp) / "missing-output"),
                parser_command=("mineru", "-p", "sample.pdf"),
            )
            result = register_document_artifacts(data_dir, ingest.id)
        self.assertEqual(result.status, "missing_output")
        self.assertEqual(result.artifacts, ())

    def test_index_document_artifacts_records_missing_sonic_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            (output_dir / "sample.md").write_text("# Sample\n\nSearchable text", encoding="utf-8")
            (output_dir / "page.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            ingest = create_document_ingest(
                data_dir,
                title="Index plan",
                input_path="sample.pdf",
                output_dir=str(output_dir),
                parser_command=("mineru", "-p", "sample.pdf", "-o", str(output_dir)),
            )
            register_document_artifacts(data_dir, ingest.id)
            env = {
                "HERMES_DATA_DIR": str(data_dir),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
                "SONIC_HOST": "",
                "SONIC_PASSWORD": "",
            }
            with patch.dict(os.environ, env, clear=False):
                result = index_document_artifacts(load_settings(), ingest.id)
            runs = list_document_index_runs(data_dir)
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.run.failed_count, 1)
        self.assertEqual(result.run.skipped_count, 1)
        self.assertEqual(runs[0]["status"], "failed")
        self.assertEqual(runs[0]["provider"], "sonic")
        self.assertEqual(runs[0]["results"][0]["status"], "missing_config")

    def test_index_document_artifacts_pushes_text_artifacts_to_sonic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            (output_dir / "sample.md").write_text("# Sample\n\nSearchable text", encoding="utf-8")
            (output_dir / "metadata.json").write_text('{"title": "Sample"}', encoding="utf-8")
            ingest = create_document_ingest(
                data_dir,
                title="Index success plan",
                input_path="sample.pdf",
                output_dir=str(output_dir),
                parser_command=("mineru", "-p", "sample.pdf", "-o", str(output_dir)),
            )
            register_document_artifacts(data_dir, ingest.id)
            env = {
                "HERMES_DATA_DIR": str(data_dir),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
                "SONIC_HOST": "127.0.0.1",
                "SONIC_PASSWORD": "secret",
            }
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.document_pipeline.sonic_push") as sonic_push:
                    sonic_push.return_value.status = "completed"
                    sonic_push.return_value.error = ""
                    result = index_document_artifacts(load_settings(), ingest.id, collection="bairui", bucket="docs", lang="zh")
            runs = list_document_index_runs(data_dir)
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.run.indexed_count, 2)
        self.assertEqual(runs[0]["collection"], "bairui")
        self.assertEqual(runs[0]["bucket"], "docs")
        self.assertEqual(sonic_push.call_count, 2)

    def test_generate_document_memory_candidates_creates_pending_review_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            (output_dir / "sample.md").write_text(
                "# Hermes Notes\n\n主人要求 Bairui Hermes 文档记忆必须先进入 pending review，不允许直接写长期记忆。",
                encoding="utf-8",
            )
            (output_dir / "page.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            ingest = create_document_ingest(
                data_dir,
                title="Memory plan",
                input_path="sample.pdf",
                output_dir=str(output_dir),
                parser_command=("mineru", "-p", "sample.pdf", "-o", str(output_dir)),
            )
            register_document_artifacts(data_dir, ingest.id)
            result = generate_document_memory_candidates(data_dir, ingest.id, max_candidates=3)
            candidates = list_document_memory_candidates(data_dir)
            audit = list_audit_events(data_dir)
        self.assertEqual(result.status, "completed")
        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(candidates[0]["status"], "pending_review")
        self.assertEqual(candidates[0]["candidate_type"], "document_fact")
        self.assertIn("pending review", candidates[0]["text"])
        self.assertEqual(candidates[0]["confidence"], 0.55)
        self.assertEqual(audit[-1]["action"], "document.memory_candidates_generated")

    def test_generate_document_memory_candidates_skips_without_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            (output_dir / "page.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            ingest = create_document_ingest(
                data_dir,
                title="Image only",
                input_path="sample.pdf",
                output_dir=str(output_dir),
                parser_command=("mineru", "-p", "sample.pdf", "-o", str(output_dir)),
            )
            register_document_artifacts(data_dir, ingest.id)
            result = generate_document_memory_candidates(data_dir, ingest.id)
        self.assertEqual(result.status, "skipped")
        self.assertEqual(result.candidates, ())
        self.assertEqual(result.skipped_count, 1)

    def test_write_obsidian_report_creates_markdown_and_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = write_obsidian_report(root / "vault", root / "data", title="Daily Brief", body="Report body")
            path = Path(report["path"])
            self.assertTrue(path.exists())
            self.assertIn("# Daily Brief", path.read_text(encoding="utf-8"))
            self.assertEqual(list_audit_events(root / "data")[0]["action"], "obsidian.report_written")

    def test_model_gateway_reports_missing_config(self):
        settings = load_settings()
        result = complete_chat(settings, "hello")
        self.assertEqual(result.status, "missing_config")

    def test_build_chat_payload(self):
        settings = load_settings()
        payload = build_chat_payload(settings, "hello", "be brief")
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertEqual(payload["messages"][1]["role"], "user")

    def test_database_status_without_url_is_missing_config(self):
        settings = load_settings()
        self.assertEqual(database_status(settings).status, "missing_config")

    def test_platform_heartbeat_uses_operational_metadata_only(self):
        settings = load_settings()
        heartbeat = build_platform_heartbeat(settings)
        self.assertEqual(heartbeat["protocol_version"], HEARTBEAT_PROTOCOL_VERSION)
        self.assertEqual(heartbeat["brand_key"], "bairui")
        self.assertEqual(heartbeat["server_id"], "missing_config")
        self.assertEqual(heartbeat["license_status"], "missing_config")
        self.assertEqual(heartbeat["database_status"], "missing_config")
        self.assertEqual(heartbeat["backup_status"], "not_configured")
        self.assertNotIn("prompt", heartbeat)
        self.assertNotIn("messages", heartbeat)

    def test_cli_parser_exposes_product_commands(self):
        parser = build_parser()
        help_text = parser.format_help()
        self.assertIn("serve", help_text)
        self.assertIn("status", help_text)
        self.assertIn("capabilities", help_text)
        self.assertIn("heartbeat", help_text)
        self.assertIn("memory", help_text)
        self.assertIn("voice", help_text)
        self.assertIn("document", help_text)
        self.assertIn("intel", help_text)
        self.assertIn("simulation", help_text)
        self.assertIn("search", help_text)
        self.assertIn("index", help_text)
        self.assertIn("runtime-readiness", help_text)

    def test_deploy_scripts_poll_readiness_and_write_json(self):
        bash_script = Path("scripts/deploy-usable.sh").read_text(encoding="utf-8")
        ps_script = Path("scripts/deploy-usable.ps1").read_text(encoding="utf-8")
        for script in (bash_script, ps_script):
            self.assertIn("/health", script)
            self.assertIn("/ready", script)
            self.assertIn("/runtime/readiness", script)
            self.assertIn("readiness.json", script)
        self.assertIn("wait_for_endpoint", bash_script)
        self.assertIn("Wait-Endpoint", ps_script)

    def test_repo_hygiene_allows_env_placeholder_passwords(self):
        hygiene_script = Path("scripts/check-repo-hygiene.ps1").read_text(encoding="utf-8")
        sonic_config = Path("infra/sonic/config.cfg").read_text(encoding="utf-8")
        self.assertIn(r"\$\{env\.", hygiene_script)
        self.assertIn('auth_password = "${env.SONIC_CHANNEL__AUTH_PASSWORD}"', sonic_config)

    def test_everos_adapter_detects_source_and_license(self):
        settings = load_settings()
        state = everos_status(settings)
        self.assertEqual(state.license, "Apache-2.0")
        self.assertIn("POST /api/v1/memory/search", state.api_contract)
        self.assertIn(state.status, {"source_ready", "configured"})

    def test_build_everos_search_payload_defaults_to_user_track(self):
        payload = build_search_payload(query="project facts", user_id="owner")
        self.assertEqual(payload["user_id"], "owner")
        self.assertEqual(payload["method"], "hybrid")
        self.assertEqual(payload["top_k"], 5)

    def test_funasr_adapter_reports_missing_config_and_openai_contract(self):
        settings = load_settings()
        state = funasr_status(settings)
        self.assertEqual(state.license, "MIT")
        self.assertEqual(state.source, "https://github.com/modelscope/FunASR")
        self.assertIn("POST /v1/audio/transcriptions", state.api_contract)
        self.assertIn("funasr-server --device cuda", state.cli_contract)
        self.assertIn(state.status, {"missing_config", "configured"})

    def test_build_funasr_server_command_uses_upstream_entrypoint(self):
        settings = load_settings()
        plan = build_funasr_server_command(settings, device="cpu", model="sensevoice")
        self.assertEqual(plan.status, "ready")
        self.assertEqual(plan.command, ("funasr-server", "--model", "sensevoice", "--device", "cpu"))

    def test_build_funasr_transcription_payload(self):
        payload = build_funasr_transcription_payload(audio_path="sample.wav", model="sensevoice", language="zh")
        self.assertEqual(payload["audio_path"], "sample.wav")
        self.assertEqual(payload["model"], "sensevoice")
        self.assertEqual(payload["language"], "zh")
        self.assertEqual(payload["response_format"], "json")

    def test_cli_voice_asr_status_prints_funasr_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "HERMES_DATA_DIR": str(Path(tmp) / "data"),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
                "FUNASR_BASE_URL": "",
            }
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.cli.print_json") as print_json:
                    code = run(["voice", "asr", "status"])
        self.assertEqual(code, 0)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["service"], "hermes")
        self.assertEqual(payload["voice_asr"]["license"], "MIT")
        self.assertEqual(payload["voice_asr"]["status"], "missing_config")

    def test_cli_voice_asr_transcribe_requires_funasr_base_url_first(self):
        with tempfile.NamedTemporaryFile(suffix=".wav") as audio:
            with tempfile.TemporaryDirectory() as tmp:
                env = {
                    "HERMES_DATA_DIR": str(Path(tmp) / "data"),
                    "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                    "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
                    "FUNASR_BASE_URL": "",
                }
                with patch.dict(os.environ, env, clear=False):
                    with patch("src.hermes.cli.print_json") as print_json:
                        code = run(["voice", "asr", "transcribe", "--audio-path", audio.name])
        self.assertEqual(code, 1)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["voice_asr"]["status"], "missing_config")

    def test_mineru_adapter_reports_missing_config_and_cli_contract(self):
        settings = load_settings()
        state = mineru_status(settings)
        self.assertEqual(state.license, "MinerU Open Source License")
        self.assertEqual(state.source, "https://github.com/opendatalab/MinerU")
        self.assertIn("mineru -p <input_path> -o <output_path>", state.cli_contract)
        self.assertIn("Markdown output for LLM-ready reading", state.output_contract)
        self.assertIn(state.status, {"missing_config", "source_ready"})

    def test_build_mineru_parse_command_uses_local_output_dir(self):
        settings = load_settings()
        plan = build_mineru_parse_command(settings, input_path="sample.pdf", backend="pipeline", language="zh")
        self.assertEqual(plan.status, "ready")
        self.assertEqual(plan.command[:4], ("mineru", "-p", "sample.pdf", "-o"))
        self.assertIn("data\\mineru-output", plan.command[4].replace("/", "\\"))
        self.assertIn("-b", plan.command)
        self.assertIn("pipeline", plan.command)
        self.assertIn("-l", plan.command)
        self.assertIn("zh", plan.command)

    def test_cli_document_parse_status_prints_mineru_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "HERMES_DATA_DIR": str(Path(tmp) / "data"),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
                "MINERU_PROJECT_ROOT": "",
                "MINERU_OUTPUT_DIR": str(Path(tmp) / "mineru-output"),
            }
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.cli.print_json") as print_json:
                    code = run(["document", "parse", "status"])
        self.assertEqual(code, 0)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["service"], "hermes")
        self.assertEqual(payload["document_parse"]["license"], "MinerU Open Source License")

    def test_cli_document_parse_command_prints_mineru_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "HERMES_DATA_DIR": str(Path(tmp) / "data"),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
                "MINERU_OUTPUT_DIR": str(Path(tmp) / "mineru-output"),
            }
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.cli.print_json") as print_json:
                    code = run(["document", "parse", "parse-command", "--input-path", "sample.pdf", "--language", "zh"])
        self.assertEqual(code, 0)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["document_parse"]["command"][:3], ("mineru", "-p", "sample.pdf"))

    def test_cli_document_ingest_plan_writes_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            env = {
                "HERMES_DATA_DIR": str(data_dir),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
                "MINERU_OUTPUT_DIR": str(Path(tmp) / "mineru-output"),
            }
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.cli.print_json") as print_json:
                    code = run(["document", "parse", "ingest-plan", "--input-path", "sample.pdf", "--title", "Sample"])
                listed = list_document_ingests(data_dir)
                with patch("src.hermes.cli.print_json") as list_print_json:
                    list_code = run(["document-ingests"])
        self.assertEqual(code, 0)
        self.assertEqual(list_code, 0)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["document_ingest"].status, "planned")
        self.assertEqual(payload["document_ingest"].pipeline["artifact_registration"], "pending")
        self.assertEqual(listed[0]["title"], "Sample")
        self.assertEqual(list_print_json.call_args.args[0]["document_ingests"][0]["title"], "Sample")

    def test_cli_document_run_ingest_executes_existing_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            ingest = create_document_ingest(
                data_dir,
                title="CLI executable plan",
                input_path="sample.pdf",
                output_dir="out",
                parser_command=("python", "-c", "print('cli mineru ok')"),
            )
            env = {
                "HERMES_DATA_DIR": str(data_dir),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
            }
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.cli.print_json") as print_json:
                    code = run(["document", "parse", "run-ingest", "--ingest-id", ingest.id, "--timeout-seconds", "10"])
                with patch("src.hermes.cli.print_json") as list_print_json:
                    list_code = run(["document-ingest-runs"])
        self.assertEqual(code, 0)
        self.assertEqual(list_code, 0)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["document_pipeline"].status, "completed")
        self.assertEqual(list_print_json.call_args.args[0]["document_ingest_runs"][0]["status"], "completed")

    def test_cli_document_register_artifacts_lists_registered_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            (output_dir / "sample.md").write_text("parsed text", encoding="utf-8")
            ingest = create_document_ingest(
                data_dir,
                title="CLI artifact plan",
                input_path="sample.pdf",
                output_dir=str(output_dir),
                parser_command=("mineru", "-p", "sample.pdf", "-o", str(output_dir)),
            )
            env = {
                "HERMES_DATA_DIR": str(data_dir),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
            }
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.cli.print_json") as print_json:
                    code = run(["document", "parse", "register-artifacts", "--ingest-id", ingest.id])
                with patch("src.hermes.cli.print_json") as list_print_json:
                    list_code = run(["document-artifacts"])
        self.assertEqual(code, 0)
        self.assertEqual(list_code, 0)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["document_artifact_registration"].status, "completed")
        self.assertEqual(payload["document_artifact_registration"].artifacts[0].artifact_type, "markdown")
        self.assertEqual(list_print_json.call_args.args[0]["document_artifacts"][0]["artifact_type"], "markdown")

    def test_cli_document_index_artifacts_lists_index_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            (output_dir / "sample.md").write_text("parsed text", encoding="utf-8")
            ingest = create_document_ingest(
                data_dir,
                title="CLI index plan",
                input_path="sample.pdf",
                output_dir=str(output_dir),
                parser_command=("mineru", "-p", "sample.pdf", "-o", str(output_dir)),
            )
            register_document_artifacts(data_dir, ingest.id)
            env = {
                "HERMES_DATA_DIR": str(data_dir),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
                "SONIC_HOST": "",
                "SONIC_PASSWORD": "",
            }
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.cli.print_json") as print_json:
                    code = run(["document", "parse", "index-artifacts", "--ingest-id", ingest.id])
                with patch("src.hermes.cli.print_json") as list_print_json:
                    list_code = run(["document-index-runs"])
        self.assertEqual(code, 1)
        self.assertEqual(list_code, 0)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["document_index"].status, "failed")
        self.assertEqual(list_print_json.call_args.args[0]["document_index_runs"][0]["status"], "failed")

    def test_cli_document_memory_candidates_lists_pending_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            (output_dir / "sample.md").write_text("Hermes 项目要求记忆候选先审核再进入 EverOS。", encoding="utf-8")
            ingest = create_document_ingest(
                data_dir,
                title="CLI memory candidate plan",
                input_path="sample.pdf",
                output_dir=str(output_dir),
                parser_command=("mineru", "-p", "sample.pdf", "-o", str(output_dir)),
            )
            register_document_artifacts(data_dir, ingest.id)
            env = {
                "HERMES_DATA_DIR": str(data_dir),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
            }
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.cli.print_json") as print_json:
                    code = run(["document", "parse", "memory-candidates", "--ingest-id", ingest.id])
                with patch("src.hermes.cli.print_json") as list_print_json:
                    list_code = run(["document-memory-candidates"])
        self.assertEqual(code, 0)
        self.assertEqual(list_code, 0)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["document_memory_candidate_generation"].status, "completed")
        self.assertEqual(list_print_json.call_args.args[0]["document_memory_candidates"][0]["status"], "pending_review")

    def test_cli_memory_status_prints_everos_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "HERMES_DATA_DIR": str(Path(tmp) / "data"),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
                "EVEROS_MEMORY_ROOT": str(Path(tmp) / "everos"),
                "EVEROS_BASE_URL": "",
            }
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.cli.print_json") as print_json:
                    code = run(["memory", "status"])
        self.assertEqual(code, 0)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["service"], "hermes")
        self.assertEqual(payload["memory"]["license"], "Apache-2.0")
        self.assertEqual(payload["memory"]["status"], "source_ready")

    def test_cli_memory_search_requires_everos_base_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "HERMES_DATA_DIR": str(Path(tmp) / "data"),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
                "EVEROS_MEMORY_ROOT": str(Path(tmp) / "everos"),
                "EVEROS_BASE_URL": "",
            }
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.cli.print_json") as print_json:
                    code = run(["memory", "search", "--query", "hello"])
        self.assertEqual(code, 1)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["memory"]["status"], "missing_config")

    def test_trendradar_adapter_detects_source_and_gpl_boundary(self):
        settings = load_settings()
        state = trendradar_status(settings)
        self.assertEqual(state.license, "GPLv3")
        self.assertIn("python -m trendradar --doctor", state.cli_contract)
        self.assertIn("HTTP MCP endpoint: /mcp", state.mcp_contract)
        self.assertIn(state.status, {"source_ready", "configured"})

    def test_build_trendradar_mcp_command_uses_real_module(self):
        settings = load_settings()
        plan = build_mcp_command(settings, transport="http", host="127.0.0.1", port=3333)
        self.assertEqual(plan.status, "ready")
        self.assertEqual(plan.command[:4], ("python", "-m", "mcp_server.server", "--transport"))
        self.assertEqual(plan.cwd, str(settings.vendor_dir / "trendradar"))

    def test_cli_intel_status_prints_trendradar_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "HERMES_DATA_DIR": str(Path(tmp) / "data"),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
                "TRENDRADAR_MCP_URL": "",
            }
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.cli.print_json") as print_json:
                    code = run(["intel", "status"])
        self.assertEqual(code, 0)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["service"], "hermes")
        self.assertEqual(payload["intelligence"]["license"], "GPLv3")
        self.assertEqual(payload["intelligence"]["status"], "source_ready")

    def test_mirofish_adapter_detects_source_and_agpl_boundary(self):
        settings = load_settings()
        state = mirofish_status(settings)
        self.assertEqual(state.license, "AGPLv3")
        self.assertIn("npm run backend", state.npm_contract)
        self.assertIn("GET /health", state.api_contract)
        self.assertIn("backend/scripts/run_parallel_simulation.py", state.simulation_scripts)
        self.assertIn(state.status, {"source_ready", "configured"})

    def test_build_mirofish_dev_command_uses_real_npm_script(self):
        settings = load_settings()
        plan = build_dev_command(settings)
        self.assertEqual(plan.status, "ready")
        self.assertEqual(plan.command, ("npm", "run", "dev"))
        self.assertEqual(plan.cwd, str(settings.vendor_dir / "mirofish"))

    def test_cli_simulation_status_prints_mirofish_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "HERMES_DATA_DIR": str(Path(tmp) / "data"),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
                "MIROFISH_BACKEND_BASE_URL": "",
            }
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.cli.print_json") as print_json:
                    code = run(["simulation", "status"])
        self.assertEqual(code, 0)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["service"], "hermes")
        self.assertEqual(payload["simulation"]["license"], "AGPLv3")
        self.assertEqual(payload["simulation"]["status"], "source_ready")

    def test_searxng_adapter_reports_missing_config_and_api_contract(self):
        settings = load_settings()
        state = searxng_status(settings)
        self.assertEqual(state.license, "AGPLv3")
        self.assertEqual(state.source, "https://github.com/searxng/searxng")
        self.assertIn("GET /search?q=<query>&format=json", state.api_contract)
        self.assertIn(state.status, {"missing_config", "configured"})

    def test_build_searxng_search_payload_uses_json_format(self):
        payload = build_searxng_search_payload(query="bairui agent", categories="general", page=2)
        self.assertEqual(payload["q"], "bairui agent")
        self.assertEqual(payload["format"], "json")
        self.assertEqual(payload["categories"], "general")
        self.assertEqual(payload["pageno"], 2)

    def test_build_searxng_docker_command_uses_official_image(self):
        settings = load_settings()
        plan = build_searxng_docker_command(settings, host_port=8080)
        self.assertEqual(plan.status, "ready")
        self.assertIn("docker.io/searxng/searxng:latest", plan.command)
        self.assertIn("8080:8080", plan.command)

    def test_cli_search_status_prints_searxng_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "HERMES_DATA_DIR": str(Path(tmp) / "data"),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
                "SEARXNG_BASE_URL": "",
            }
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.cli.print_json") as print_json:
                    code = run(["search", "status"])
        self.assertEqual(code, 0)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["service"], "hermes")
        self.assertEqual(payload["search"]["license"], "AGPLv3")
        self.assertEqual(payload["search"]["status"], "missing_config")

    def test_cli_search_query_requires_searxng_base_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "HERMES_DATA_DIR": str(Path(tmp) / "data"),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
                "SEARXNG_BASE_URL": "",
            }
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.cli.print_json") as print_json:
                    code = run(["search", "query", "--query", "hello"])
        self.assertEqual(code, 1)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["search"]["status"], "missing_config")

    def test_sonic_adapter_reports_missing_config_and_protocol_contract(self):
        settings = load_settings()
        state = sonic_status(settings)
        self.assertEqual(state.license, "MPL-2.0")
        self.assertEqual(state.source, "https://github.com/valeriansaliou/sonic")
        self.assertIn("TCP channel protocol on port 1491", state.protocol_contract)
        self.assertIn(state.status, {"missing_config", "configured"})

    def test_build_sonic_query_payload(self):
        payload = build_sonic_query_payload(collection="bairui", bucket="docs", query="agent memory", limit=7, lang="zh")
        self.assertEqual(payload["collection"], "bairui")
        self.assertEqual(payload["bucket"], "docs")
        self.assertEqual(payload["query"], "agent memory")
        self.assertEqual(payload["limit"], 7)
        self.assertEqual(payload["lang"], "zh")

    def test_build_sonic_docker_command_mounts_config(self):
        settings = load_settings()
        plan = build_sonic_docker_command(settings, host_port=1491)
        self.assertEqual(plan.status, "ready")
        self.assertIn("valeriansaliou/sonic:latest", plan.command)
        self.assertIn("$(pwd)/infra/sonic/config.cfg:/etc/sonic.cfg", plan.command)
        self.assertIn("127.0.0.1:1491:1491", plan.command)

    def test_cli_index_status_prints_sonic_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "HERMES_DATA_DIR": str(Path(tmp) / "data"),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
                "SONIC_HOST": "",
                "SONIC_PASSWORD": "",
            }
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.cli.print_json") as print_json:
                    code = run(["index", "status"])
        self.assertEqual(code, 0)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["service"], "hermes")
        self.assertEqual(payload["index"]["license"], "MPL-2.0")
        self.assertEqual(payload["index"]["status"], "missing_config")

    def test_cli_index_query_requires_sonic_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "HERMES_DATA_DIR": str(Path(tmp) / "data"),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
                "SONIC_HOST": "",
                "SONIC_PASSWORD": "",
            }
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.cli.print_json") as print_json:
                    code = run(["index", "query", "--collection", "bairui", "--bucket", "docs", "--query", "hello"])
        self.assertEqual(code, 1)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["index"]["status"], "missing_config")

    def test_runtime_readiness_reports_required_blockers_and_optional_warnings(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "HERMES_DATA_DIR": str(Path(tmp) / "data"),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
                "EVEROS_BASE_URL": "",
                "SEARXNG_BASE_URL": "",
                "SONIC_HOST": "",
                "SONIC_PASSWORD": "",
            }
            with patch.dict(os.environ, env, clear=False):
                readiness = collect_runtime_readiness(load_settings())
        self.assertIn(readiness["status"], {"partial", "blocked"})
        names = {item["name"] for item in readiness["items"]}
        self.assertIn("everos_memory", names)
        self.assertIn("funasr_voice_asr", names)
        self.assertIn("mineru_document_parse", names)
        self.assertIn("sonic_local_index", names)
        self.assertTrue(any("funasr_voice_asr" in warning for warning in readiness["warnings"]))
        self.assertTrue(any("mineru_document_parse" in warning for warning in readiness["warnings"]))
        self.assertTrue(any("sonic_local_index" in warning for warning in readiness["warnings"]))

    def test_cli_status_prints_runtime_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"HERMES_DATA_DIR": str(Path(tmp) / "data"), "HERMES_LOG_DIR": str(Path(tmp) / "logs"), "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault")}, clear=False):
                with patch("src.hermes.cli.print_json") as print_json:
                    code = run(["status"])
        self.assertEqual(code, 0)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["service"], "hermes")
        self.assertEqual(payload["brand_key"], "bairui")
        self.assertEqual(payload["database"].status, "missing_config")

    def test_cli_job_creates_file_backed_job(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            with patch.dict(os.environ, {"HERMES_DATA_DIR": str(data_dir), "HERMES_LOG_DIR": str(Path(tmp) / "logs"), "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault")}, clear=False):
                with patch("src.hermes.cli.print_json") as print_json:
                    code = run(["job", "--title", "CLI task", "--prompt", "do work", "--route", "ops"])
            jobs_file_exists = (data_dir / "jobs.jsonl").exists()
        self.assertEqual(code, 0)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["job"].title, "CLI task")
        self.assertEqual(payload["job"].route, "ops")
        self.assertTrue(jobs_file_exists)

    def test_cli_chat_missing_config_returns_failure_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"HERMES_DATA_DIR": str(Path(tmp) / "data"), "HERMES_LOG_DIR": str(Path(tmp) / "logs"), "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"), "BAIRUI_MODEL_BASE_URL": "", "BAIRUI_MODEL_API_KEY": "", "BAIRUI_MODEL_NAME": ""}, clear=False):
                with patch("src.hermes.cli.print_json") as print_json:
                    code = run(["chat", "--prompt", "hello"])
        self.assertEqual(code, 1)
        self.assertEqual(print_json.call_args.args[0]["chat"].status, "missing_config")


if __name__ == "__main__":
    unittest.main()
