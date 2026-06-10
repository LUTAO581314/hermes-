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
from src.hermes.adapters.everos import build_search_payload, status as everos_status
from src.hermes.adapters.mirofish import build_dev_command, status as mirofish_status
from src.hermes.adapters.trendradar import build_mcp_command, status as trendradar_status
from src.hermes.license import load_license, sign_license_payload
from src.hermes.model_gateway import build_chat_payload, complete_chat
from src.hermes.platform import HEARTBEAT_PROTOCOL_VERSION, build_platform_heartbeat
from src.hermes.storage import create_job, list_audit_events, list_jobs, write_obsidian_report


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
        self.assertIn("intel", help_text)
        self.assertIn("simulation", help_text)

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
