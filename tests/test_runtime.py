import json
import os
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from src.hermes.capabilities import collect_capabilities
from src.hermes.avatar import avatar_engine_status, build_avatar_manifest, set_avatar_state, validate_avatar_model
from src.hermes.agents import add_agent_user_message, create_agent_session, list_agent_events, list_agent_events_page, list_agent_promotions, list_agent_sessions, list_agents, promote_agent_event, retry_agent_event, run_agent_round, update_agent_session
from src.hermes.channels import (
    channel_status,
    channel_targets,
    diagnose_channel_targets,
    list_channel_approvals,
    plan_channel_send,
    review_channel_approval,
)
from src.hermes.codegraph import codegraph_impact, codegraph_overview, codegraph_status, query_codegraph, register_codegraph_repo, scan_codegraph_repo
from src.hermes.cli import build_parser, run
from src.hermes.config import load_settings
from src.hermes.db import SCHEMA_SQL, database_status
from src.hermes.demo import seed_demo_data
from src.hermes.demo_flow import run_demo_flow
from src.hermes.document_pipeline import build_document_ingest_session_summary, build_document_workbench_state, create_document_ingest_report, create_document_source_refs, execute_document_workbench_next, generate_document_memory_candidates, index_document_artifacts, list_document_ingest_session_summaries, list_pending_document_memory_reviews, register_document_artifacts, review_document_memory_candidate, review_document_memory_candidates_batch, run_document_ingest, run_document_workbench_until_blocked
from src.hermes.events import audit_event_to_frontend_event, build_sse_frame, list_frontend_events
from src.hermes.frontend_contract import build_frontend_contract
from src.hermes.adapters.everos import EverOSResult, build_search_payload, status as everos_status
from src.hermes.adapters.funasr import build_server_command as build_funasr_server_command, build_transcription_payload as build_funasr_transcription_payload, status as funasr_status
from src.hermes.adapters.mineru import build_parse_command as build_mineru_parse_command, status as mineru_status
from src.hermes.adapters.mirofish import build_dev_command, status as mirofish_status
from src.hermes.adapters.searxng import build_docker_command as build_searxng_docker_command, build_search_payload as build_searxng_search_payload, status as searxng_status
from src.hermes.adapters.sonic import SonicResult, build_docker_command as build_sonic_docker_command, build_query_payload as build_sonic_query_payload, status as sonic_status
from src.hermes.adapters.trendradar import build_mcp_command, status as trendradar_status
from src.hermes.license import load_license, sign_license_payload
from src.hermes.model_gateway import build_chat_payload, complete_chat
from src.hermes.platform import HEARTBEAT_PROTOCOL_VERSION, build_platform_heartbeat
from src.hermes.runtime_readiness import collect_runtime_readiness
from src.hermes.server import HermesHandler, PUBLIC_SERVICE
from src.hermes.storage import (
    create_document_ingest,
    create_job,
    list_audit_events,
    list_channel_approval_requests,
    list_channel_approval_reviews,
    list_document_artifacts,
    list_document_index_runs,
    list_document_ingest_reports,
    list_document_ingest_runs,
    list_document_ingests,
    list_document_memory_candidates,
    list_document_memory_reviews,
    list_jobs,
    list_reports,
    list_source_refs,
    write_obsidian_report,
)


def _http_get(port: int, path: str) -> tuple[int, dict[str, str], bytes]:
    connection = HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        body = response.read()
        headers = {key.lower(): value for key, value in response.getheaders()}
        return response.status, headers, body
    finally:
        connection.close()


def _http_post(port: int, path: str, payload: dict[str, object] | None = None) -> tuple[int, dict[str, str], bytes]:
    body = json.dumps(payload or {}).encode("utf-8")
    connection = HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request("POST", path, body=body, headers={"Content-Type": "application/json"})
        response = connection.getresponse()
        response_body = response.read()
        headers = {key.lower(): value for key, value in response.getheaders()}
        return response.status, headers, response_body
    finally:
        connection.close()


class RuntimeFoundationTests(unittest.TestCase):
    def test_load_settings_defaults(self):
        settings = load_settings()
        self.assertEqual(settings.product_name, "bairui Agent OS")
        self.assertEqual(settings.brand_key, "bairui")
        self.assertEqual(settings.trademark_name, "bairui")
        self.assertEqual(settings.logo_text, "bairui")
        self.assertEqual(settings.port, 8787)
        self.assertEqual(settings.avatar_engine_package, "pixi-live2d-display-advanced")
        self.assertEqual(settings.avatar_engine_version, "^1.1.0")

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
        self.assertIn("bairui_avatar_runtime", names)
        self.assertIn("bairui_codegraph", names)
        self.assertIn("bairui_agents", names)

    def test_frontend_contract_lists_stable_product_surfaces(self):
        contract = build_frontend_contract(load_settings(), "test-version")
        screens = {screen["id"]: screen for screen in contract["screens"]}
        api_groups = {group["id"]: group for group in contract["api_groups"]}
        document_paths = {endpoint["path"] for endpoint in api_groups["document_workbench"]["endpoints"]}
        operation_paths = {endpoint["path"] for endpoint in api_groups["operations"]["endpoints"]}
        channel_paths = {endpoint["path"] for endpoint in api_groups["channels"]["endpoints"]}
        codegraph_paths = {endpoint["path"] for endpoint in api_groups["codegraph"]["endpoints"]}
        agent_paths = {endpoint["path"] for endpoint in api_groups["agents"]["endpoints"]}
        serialized = json.dumps(contract, ensure_ascii=False)
        forbidden = (
            "Hermes",
            "hermes",
            "MOXI",
            "Moxi",
            "Brain UI",
            "EverOS",
            "MinerU",
            "Sonic",
            "SearXNG",
            "FunASR",
            "MiroFish",
            "TrendRadar",
            "Xiaobailong",
            "Bailongma",
            "小白龙",
            "白龙马",
        )
        for brand in forbidden:
            self.assertNotIn(brand, serialized)
        self.assertEqual(contract["service"], "bairui")
        self.assertEqual(contract["product"]["brand_key"], "bairui")
        self.assertEqual(contract["visibility_policy"]["public_brand"], "bairui")
        self.assertIn("activation", screens)
        self.assertIn("/jobs", screens["dashboard"]["read"])
        self.assertIn("/audit", screens["dashboard"]["read"])
        self.assertIn("/events", screens["dashboard"]["read"])
        self.assertIn("/demo/seed", {action["path"] for action in screens["dashboard"]["actions"]})
        self.assertIn("/demo/flow", {action["path"] for action in screens["dashboard"]["actions"]})
        self.assertFalse(contract["forms"]["demo_seed"]["safety"]["will_send"])
        self.assertFalse(contract["forms"]["demo_seed"]["safety"]["will_write_long_term_memory"])
        self.assertFalse(contract["forms"]["demo_flow"]["safety"]["will_send"])
        self.assertFalse(contract["forms"]["demo_flow"]["safety"]["will_write_long_term_memory"])
        self.assertTrue(contract["forms"]["demo_flow"]["safety"]["uses_real_contracts"])
        self.assertIn("document_ingest", screens)
        self.assertIn("channels", screens)
        self.assertIn("avatar", screens)
        self.assertIn("/channels/status", screens["channels"]["read"])
        self.assertIn("/channels/targets", screens["channels"]["read"])
        self.assertIn("/channels/diagnostics", screens["channels"]["read"])
        self.assertIn("/channels/approvals", screens["channels"]["read"])
        self.assertIn("/channels/approvals/reviews", screens["channels"]["read"])
        self.assertIn("channel_send", contract["forms"])
        self.assertIn("channel_approval_review", contract["forms"])
        self.assertIn("/document/parse/session-list", screens["document_ingest"]["read"])
        self.assertIn("/document/parse/session-summary", screens["document_ingest"]["read"])
        self.assertIn("document_ingest_plan", contract["forms"])
        self.assertIn("/document/parse/source-refs", {action["path"] for action in screens["document_ingest"]["actions"]})
        self.assertIn("/document/parse/ingest-report", {action["path"] for action in screens["document_ingest"]["actions"]})
        self.assertIn("job_create", contract["forms"])
        self.assertGreaterEqual(len(contract["activation_flow"]), 7)
        self.assertIn("/jobs", operation_paths)
        self.assertIn("/demo/flow", operation_paths)
        self.assertIn("/audit", operation_paths)
        self.assertIn("/events", operation_paths)
        self.assertIn("/channels/send", channel_paths)
        self.assertIn("/channels/diagnostics", channel_paths)
        self.assertIn("/channels/approvals", channel_paths)
        self.assertIn("/channels/approvals/reviews", channel_paths)
        self.assertIn("/channels/approvals/review", channel_paths)
        self.assertIn("avatar", api_groups)
        self.assertIn("/avatar/status", {endpoint["path"] for endpoint in api_groups["avatar"]["endpoints"]})
        self.assertIn("/avatar/manifest", screens["avatar"]["read"])
        self.assertIn("/document/parse/workbench-next", document_paths)
        self.assertIn("/document/parse/source-refs", document_paths)
        self.assertIn("/document/parse/ingest-report", document_paths)
        self.assertIn("codegraph", screens)
        self.assertIn("/codegraph/status", screens["codegraph"]["read"])
        self.assertIn("codegraph_repo_register", contract["forms"])
        self.assertIn("/codegraph/query", codegraph_paths)
        self.assertIn("agent_session_create", contract["forms"])
        self.assertIn("agent_session_title", contract["forms"])
        self.assertIn("agent_message_append", contract["forms"])
        self.assertFalse(contract["forms"]["agent_retry"]["safety"]["will_execute_external_action"])
        self.assertFalse(contract["forms"]["agent_promotion"]["safety"]["will_execute_external_action"])
        self.assertEqual(contract["forms"]["agent_promotion"]["safety"]["idempotency_key"], "event_id + target")
        self.assertIn("/agents", screens["chat"]["read"])
        self.assertIn("/agents/session/{session_id}/message", agent_paths)
        self.assertIn("/agents/session/{session_id}/title", agent_paths)
        self.assertIn("/agents/session/{session_id}/round", agent_paths)
        self.assertIn("/agents/session/{session_id}/events", agent_paths)
        self.assertIn("/agents/session/{session_id}/retry", agent_paths)
        self.assertIn("needs_review", contract["state_values"])
        self.assertIn("approval_required", contract["state_values"])
        self.assertIn("speaking", contract["state_values"])

    def test_codegraph_scans_source_structure_without_memory_promotion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            package = repo / "src" / "demo"
            package.mkdir(parents=True)
            (package / "__init__.py").write_text("", encoding="utf-8")
            (package / "service.py").write_text(
                "\n".join(
                    [
                        "import json",
                        "from pathlib import Path",
                        "",
                        "class Worker:",
                        "    def run(self):",
                        "        return Path('.')",
                        "",
                        "def helper():",
                        "    return json.dumps({'ok': True})",
                    ]
                ),
                encoding="utf-8",
            )
            env = {
                "HERMES_DATA_DIR": str(root / "data"),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
                "BAIRUI_CODEGRAPH_ROOT": str(root / "codegraph"),
            }
            with patch.dict(os.environ, env, clear=False):
                settings = load_settings()
                registered = register_codegraph_repo(settings, str(repo), name="demo")
                scan = scan_codegraph_repo(settings, registered.id)
                overview = codegraph_overview(settings, repo_id=registered.id)
                query = query_codegraph(settings, "helper", repo_id=registered.id)
                impact = codegraph_impact(settings, "service.py", repo_id=registered.id)
                status = codegraph_status(settings)

        self.assertEqual(registered.name, "demo")
        self.assertEqual(scan["status"], "completed")
        self.assertGreaterEqual(scan["scan"]["file_count"], 2)
        self.assertTrue(any(symbol["name"] == "Worker" for symbol in overview["top_symbols"]))
        self.assertTrue(any(result["name"] == "helper" for result in query["results"]))
        self.assertEqual(impact["status"], "completed")
        self.assertIn("does not write long-term memory", status.memory_boundary)

    def test_cli_codegraph_register_scan_and_query(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            (repo / "app.py").write_text("def boot():\n    return 'ok'\n", encoding="utf-8")
            env = {
                "HERMES_DATA_DIR": str(root / "data"),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
                "BAIRUI_CODEGRAPH_ROOT": str(root / "codegraph"),
            }
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.cli.print_json") as print_json:
                    code = run(["codegraph", "register", "--path", str(repo), "--name", "demo"])
                    repo_id = print_json.call_args.args[0]["codegraph_repo"]["id"]
                with patch("src.hermes.cli.print_json") as print_json:
                    scan_code = run(["codegraph", "scan", "--repo-id", repo_id])
                    scan_payload = print_json.call_args.args[0]
                with patch("src.hermes.cli.print_json") as print_json:
                    query_code = run(["codegraph", "query", "--query", "boot", "--repo-id", repo_id])
                    query_payload = print_json.call_args.args[0]
        self.assertEqual(code, 0)
        self.assertEqual(scan_code, 0)
        self.assertEqual(scan_payload["codegraph_scan"]["status"], "completed")
        self.assertEqual(query_code, 0)
        self.assertEqual(query_payload["codegraph_query"]["results"][0]["name"], "boot")

    def test_codegraph_overview_http_supports_repo_filter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo_a = root / "repo-a"
            repo_b = root / "repo-b"
            repo_a.mkdir()
            repo_b.mkdir()
            (repo_a / "alpha.py").write_text("def alpha():\n    return 'a'\n", encoding="utf-8")
            (repo_b / "beta.py").write_text("def beta():\n    return 'b'\n", encoding="utf-8")
            env = {
                "HERMES_DATA_DIR": str(root / "data"),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
                "BAIRUI_CODEGRAPH_ROOT": str(root / "codegraph"),
            }
            with patch.dict(os.environ, env, clear=False):
                server = ThreadingHTTPServer(("127.0.0.1", 0), HermesHandler)
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    _, _, register_a_body = _http_post(server.server_port, "/codegraph/repos/register", {"path": str(repo_a), "name": "alpha"})
                    _, _, register_b_body = _http_post(server.server_port, "/codegraph/repos/register", {"path": str(repo_b), "name": "beta"})
                    repo_a_id = json.loads(register_a_body.decode("utf-8"))["codegraph_repo"]["id"]
                    repo_b_id = json.loads(register_b_body.decode("utf-8"))["codegraph_repo"]["id"]
                    scan_a_status, _, _ = _http_post(server.server_port, "/codegraph/repos/scan", {"repo_id": repo_a_id})
                    overview_status, _, overview_body = _http_get(server.server_port, f"/codegraph/overview?repo_id={repo_a_id}")
                    empty_status, _, empty_body = _http_get(server.server_port, f"/codegraph/overview?repo_id={repo_b_id}")
                    overview = json.loads(overview_body.decode("utf-8"))["codegraph"]
                    empty = json.loads(empty_body.decode("utf-8"))["codegraph"]
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join(timeout=2)

        self.assertEqual(scan_a_status, 200)
        self.assertEqual(overview_status, 200)
        self.assertEqual(empty_status, 200)
        self.assertEqual(overview["status"], "ready")
        self.assertEqual(overview["scan"]["repo_id"], repo_a_id)
        self.assertEqual(empty["status"], "empty")

    def test_agents_roster_and_round_keep_permissions_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "HERMES_DATA_DIR": str(Path(tmp) / "data"),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
                "BAIRUI_MODEL_BASE_URL": "",
                "BAIRUI_MODEL_API_KEY": "",
                "BAIRUI_MODEL_NAME": "",
            }
            with patch.dict(os.environ, env, clear=False):
                settings = load_settings()
                agents = list_agents(settings)
                session = create_agent_session(settings, "ops", ("coordinator", "memory", "operator"))
                result = run_agent_round(settings, session.id, "summarize current state")
                events = list_agent_events(settings, session_id=session.id)
                promotion = promote_agent_event(settings, events[-1]["id"], "job")

        by_id = {agent.id: agent for agent in agents}
        self.assertEqual(by_id["coordinator"].status, "missing_config")
        self.assertEqual(by_id["memory"].permission, "approval_required")
        self.assertEqual(result["status"], "completed")
        statuses = {event["agent_id"]: event["status"] for event in events}
        self.assertEqual(statuses["coordinator"], "missing_config")
        self.assertEqual(statuses["memory"], "approval_required")
        self.assertEqual(statuses["operator"], "completed")
        self.assertEqual(promotion["status"], "planned")
        self.assertFalse(promotion["will_execute_external_action"])

    def test_agent_event_promotions_create_reviewable_resources(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "HERMES_DATA_DIR": str(Path(tmp) / "data"),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
                "BAIRUI_MODEL_BASE_URL": "",
                "BAIRUI_MODEL_API_KEY": "",
                "BAIRUI_MODEL_NAME": "",
            }
            with patch.dict(os.environ, env, clear=False):
                settings = load_settings()
                session = create_agent_session(settings, "ops", ("operator",))
                run_agent_round(settings, session.id, "promote this")
                event = list_agent_events(settings, session_id=session.id)[-1]
                job = promote_agent_event(settings, event["id"], "job")
                job_again = promote_agent_event(settings, event["id"], "job")
                report = promote_agent_event(settings, event["id"], "report")
                memory = promote_agent_event(settings, event["id"], "memory_review")
                channel = promote_agent_event(settings, event["id"], "channel_draft")

                jobs = list_jobs(settings.data_dir)
                reports = list_reports(settings.data_dir)
                candidates = list_document_memory_candidates(settings.data_dir)
                approvals = list_channel_approval_requests(settings.data_dir)
                promotions = list_agent_promotions(settings, session_id=session.id)
                audit = list_audit_events(settings.data_dir, limit=50)

        self.assertEqual(job["created_resource"]["type"], "job")
        self.assertEqual(job_again["status"], "duplicate")
        self.assertTrue(job_again["duplicate"])
        self.assertEqual(job_again["created_resource"]["id"], job["created_resource"]["id"])
        self.assertEqual(job["created_resource"]["source"]["source_ref"], event["id"])
        self.assertEqual(job["created_resource"]["source"]["session_id"], session.id)
        self.assertEqual(job["created_resource"]["source"]["target"], "job")
        self.assertEqual(report["created_resource"]["type"], "report")
        self.assertEqual(report["created_resource"]["source"]["source_type"], "agent_event")
        self.assertEqual(memory["created_resource"]["type"], "document_memory_candidate")
        self.assertTrue(memory["created_resource"]["review_required"])
        self.assertEqual(memory["created_resource"]["source"]["target"], "memory_review")
        self.assertEqual(channel["created_resource"]["type"], "channel_approval_request")
        self.assertTrue(channel["created_resource"]["review_required"])
        self.assertEqual(channel["created_resource"]["source"]["target"], "channel_draft")
        self.assertEqual(len(promotions), 4)
        self.assertEqual({item["target"] for item in promotions}, {"job", "report", "memory_review", "channel_draft"})
        self.assertEqual(promotions[0]["event_id"], event["id"])
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[-1]["id"], job["created_resource"]["id"])
        self.assertEqual(reports[-1]["id"], report["created_resource"]["id"])
        self.assertEqual(candidates[-1]["id"], memory["created_resource"]["id"])
        self.assertEqual(approvals[-1]["id"], channel["created_resource"]["id"])
        promoted = [event for event in audit if event["action"] == "agent.event_promoted"]
        reused = [event for event in audit if event["action"] == "agent.event_promotion_reused"]
        self.assertTrue(all(event["payload"]["promotion_id"] for event in promoted))
        self.assertEqual(reused[-1]["payload"]["duplicate"], True)

    def test_agent_sessions_support_title_message_paging_and_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "HERMES_DATA_DIR": str(Path(tmp) / "data"),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
                "BAIRUI_MODEL_BASE_URL": "",
                "BAIRUI_MODEL_API_KEY": "",
                "BAIRUI_MODEL_NAME": "",
            }
            with patch.dict(os.environ, env, clear=False):
                settings = load_settings()
                session = create_agent_session(settings, "draft title", ("coordinator", "operator"))
                renamed = update_agent_session(settings, session.id, title="Research cockpit")
                message = add_agent_user_message(settings, session.id, "Investigate onboarding blockers.")
                round_result = run_agent_round(settings, session.id, "Investigate onboarding blockers.")
                page_one = list_agent_events_page(settings, session_id=session.id, limit=2, offset=0)
                page_two = list_agent_events_page(settings, session_id=session.id, limit=2, offset=2)
                missing_config_event = next(event for event in list_agent_events(settings, session_id=session.id) if event["status"] == "missing_config")
                retry = retry_agent_event(settings, missing_config_event["id"])
                sessions = list_agent_sessions(settings)

        self.assertEqual(renamed["status"], "completed")
        self.assertEqual(sessions[-1]["title"], "Research cockpit")
        self.assertEqual(message["status"], "completed")
        self.assertEqual(message["event"]["agent_id"], "owner")
        self.assertIn(round_result["status"], {"completed", "partial"})
        self.assertEqual(page_one["pagination"]["total"], 3)
        self.assertEqual(page_one["pagination"]["next_offset"], 2)
        self.assertEqual(page_two["pagination"]["previous_offset"], 0)
        self.assertEqual(retry["status"], "partial")
        self.assertEqual(retry["event"]["status"], "missing_config")
        self.assertFalse(retry["will_execute_external_action"])

    def test_agent_session_http_controls_are_real_contracts(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "HERMES_DATA_DIR": str(Path(tmp) / "data"),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
                "BAIRUI_MODEL_BASE_URL": "",
                "BAIRUI_MODEL_API_KEY": "",
                "BAIRUI_MODEL_NAME": "",
            }
            with patch.dict(os.environ, env, clear=False):
                server = ThreadingHTTPServer(("127.0.0.1", 0), HermesHandler)
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    create_status, _, create_body = _http_post(
                        server.server_port,
                        "/agents/session",
                        {"title": "first", "agent_ids": ["coordinator", "operator"]},
                    )
                    session = json.loads(create_body.decode("utf-8"))["agent_session"]
                    title_status, _, title_body = _http_post(server.server_port, f"/agents/session/{session['id']}/title", {"title": "Renamed session"})
                    message_status, _, message_body = _http_post(
                        server.server_port,
                        f"/agents/session/{session['id']}/message",
                        {"content": "Investigate current workspace."},
                    )
                    round_status, _, _ = _http_post(
                        server.server_port,
                        f"/agents/session/{session['id']}/round",
                        {"prompt": "Investigate current workspace."},
                    )
                    events_status, _, events_body = _http_post(
                        server.server_port,
                        f"/agents/session/{session['id']}/events",
                        {"limit": 2, "offset": 0},
                    )
                    events_page = json.loads(events_body.decode("utf-8"))["agent_events_page"]
                    missing = next(event for event in list_agent_events(load_settings(), session_id=session["id"]) if event["status"] == "missing_config")
                    operator_event = next(event for event in list_agent_events(load_settings(), session_id=session["id"]) if event["agent_id"] == "operator")
                    promote_status, _, _ = _http_post(
                        server.server_port,
                        f"/agents/session/{session['id']}/promote",
                        {"event_id": operator_event["id"], "target": "report"},
                    )
                    promotions_status, _, promotions_body = _http_get(server.server_port, f"/agents/session/{session['id']}/promotions")
                    promotions = json.loads(promotions_body.decode("utf-8"))["agent_promotions"]
                    retry_status, _, retry_body = _http_post(
                        server.server_port,
                        f"/agents/session/{session['id']}/retry",
                        {"event_id": missing["id"]},
                    )
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join(timeout=2)

        self.assertEqual(create_status, 201)
        self.assertEqual(title_status, 200)
        self.assertEqual(json.loads(title_body.decode("utf-8"))["agent_session_update"]["session"]["title"], "Renamed session")
        self.assertEqual(message_status, 200)
        self.assertEqual(json.loads(message_body.decode("utf-8"))["agent_message"]["event"]["agent_id"], "owner")
        self.assertEqual(round_status, 200)
        self.assertEqual(events_status, 200)
        self.assertEqual(events_page["pagination"]["limit"], 2)
        self.assertGreaterEqual(events_page["pagination"]["total"], 3)
        self.assertEqual(promote_status, 200)
        self.assertEqual(promotions_status, 200)
        self.assertEqual(promotions[-1]["resource_type"], "report")
        self.assertEqual(promotions[-1]["source"]["source_type"], "agent_event")
        self.assertEqual(retry_status, 200)
        self.assertFalse(json.loads(retry_body.decode("utf-8"))["agent_retry"]["will_execute_external_action"])

    def test_demo_seed_creates_walkthrough_resources_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "HERMES_DATA_DIR": str(Path(tmp) / "data"),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
            }
            with patch.dict(os.environ, env, clear=False):
                settings = load_settings()
                first = seed_demo_data(settings)
                second = seed_demo_data(settings)
                jobs = list_jobs(settings.data_dir)
                reports = list_reports(settings.data_dir)
                candidates = list_document_memory_candidates(settings.data_dir)
                approvals = list_channel_approval_requests(settings.data_dir)

        self.assertEqual(first["status"], "completed")
        self.assertEqual(second["status"], "skipped")
        self.assertEqual(jobs[-1]["title"], "Demo research task")
        self.assertEqual(reports[-1]["title"], "Demo onboarding report")
        self.assertEqual(candidates[-1]["candidate_type"], "customer_preference")
        self.assertEqual(approvals[-1]["target_id"], "owner_review")
        self.assertFalse(first["audit_marker"]["payload"]["will_send"])
        self.assertFalse(first["audit_marker"]["payload"]["will_write_long_term_memory"])

    def test_demo_seed_http_endpoint_is_safe_and_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "HERMES_DATA_DIR": str(Path(tmp) / "data"),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
            }
            with patch.dict(os.environ, env, clear=False):
                server = ThreadingHTTPServer(("127.0.0.1", 0), HermesHandler)
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    first_status, _, first_body = _http_post(server.server_port, "/demo/seed")
                    second_status, _, second_body = _http_post(server.server_port, "/demo/seed")
                    settings = load_settings()
                    jobs = list_jobs(settings.data_dir)
                    approvals = list_channel_approval_requests(settings.data_dir)
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join(timeout=2)

        first = json.loads(first_body.decode("utf-8"))
        second = json.loads(second_body.decode("utf-8"))
        self.assertEqual(first_status, 201)
        self.assertEqual(second_status, 200)
        self.assertEqual(first["demo_seed"]["status"], "completed")
        self.assertEqual(second["demo_seed"]["status"], "skipped")
        self.assertFalse(first["demo_seed"]["audit_marker"]["payload"]["will_send"])
        self.assertFalse(first["demo_seed"]["audit_marker"]["payload"]["will_write_long_term_memory"])
        self.assertEqual(len(jobs), 1)
        self.assertEqual(len(approvals), 1)

    def test_demo_flow_runs_product_closure_without_external_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = {
                "HERMES_DATA_DIR": str(root / "data"),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
                "BAIRUI_CODEGRAPH_ROOT": str(root / "codegraph"),
                "BAIRUI_CHANNELS_ENABLED": "1",
            }
            with patch.dict(os.environ, env, clear=False):
                result = run_demo_flow(load_settings())

        self.assertEqual(result["status"], "completed")
        self.assertTrue(all(result["checkpoints"].values()))
        self.assertEqual(result["promotions"]["report"]["status"], "planned")
        self.assertEqual(result["channel"]["plan"]["status"], "approval_required")
        self.assertFalse(result["channel"]["plan"]["will_send"])
        self.assertEqual(result["channel"]["review"]["status"], "reviewed")
        self.assertFalse(result["channel"]["review"]["will_send"])
        self.assertEqual(result["memory"]["review"]["status"], "rejected")
        self.assertFalse(result["memory"]["will_write_long_term_memory"])
        self.assertEqual(result["codegraph"]["query"]["status"], "completed")
        self.assertIn("does not write long-term memory", result["codegraph"]["memory_boundary"])

    def test_cli_demo_flow_exits_success_when_checkpoints_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = {
                "HERMES_DATA_DIR": str(root / "data"),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
                "BAIRUI_CODEGRAPH_ROOT": str(root / "codegraph"),
                "BAIRUI_CHANNELS_ENABLED": "1",
            }
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.cli.print_json") as print_json:
                    code = run(["demo", "flow"])
                    payload = print_json.call_args.args[0]["demo_flow"]

        self.assertEqual(code, 0)
        self.assertEqual(payload["status"], "completed")
        self.assertTrue(payload["checkpoints"]["no_external_send"])
        self.assertTrue(payload["checkpoints"]["no_auto_memory_write"])

    def test_demo_flow_http_endpoint_runs_safe_product_closure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = {
                "HERMES_DATA_DIR": str(root / "data"),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
                "BAIRUI_CODEGRAPH_ROOT": str(root / "codegraph"),
                "BAIRUI_CHANNELS_ENABLED": "1",
            }
            with patch.dict(os.environ, env, clear=False):
                server = ThreadingHTTPServer(("127.0.0.1", 0), HermesHandler)
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    status, _, body = _http_post(server.server_port, "/demo/flow")
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join(timeout=2)

        payload = json.loads(body.decode("utf-8"))["demo_flow"]
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "completed")
        self.assertTrue(payload["checkpoints"]["command_session"])
        self.assertTrue(payload["checkpoints"]["channel_review_recorded"])
        self.assertTrue(payload["checkpoints"]["codegraph_query_ready"])
        self.assertFalse(payload["channel"]["plan"]["will_send"])
        self.assertFalse(payload["memory"]["will_write_long_term_memory"])

    def test_console_static_assets_are_served_by_backend(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "HERMES_DATA_DIR": str(Path(tmp) / "data"),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
            }
            with patch.dict(os.environ, env, clear=False):
                server = ThreadingHTTPServer(("127.0.0.1", 0), HermesHandler)
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    html_status, html_headers, html_body = _http_get(server.server_port, "/console")
                    js_status, js_headers, js_body = _http_get(server.server_port, "/console/app.js")
                    css_status, css_headers, css_body = _http_get(server.server_port, "/console/styles.css")
                    escape_status, _, escape_body = _http_get(server.server_port, "/console/../README.md")
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join(timeout=2)

        self.assertEqual(html_status, 200)
        self.assertIn("text/html", html_headers["content-type"])
        self.assertIn(b"bairui Console", html_body)
        self.assertEqual(js_status, 200)
        self.assertIn("text/javascript", js_headers["content-type"])
        self.assertIn(b"/frontend/contract", js_body)
        self.assertEqual(css_status, 200)
        self.assertIn("text/css", css_headers["content-type"])
        self.assertEqual(escape_status, 403)
        self.assertIn(b"forbidden", escape_body)

    def test_console_product_errors_explain_next_steps_and_safety(self):
        app_js = Path("web/bairui-console/app.js").read_text(encoding="utf-8")
        styles = Path("web/bairui-console/styles.css").read_text(encoding="utf-8")

        self.assertIn("function productErrorGuide", app_js)
        self.assertIn("function renderProductError", app_js)
        self.assertIn("Register a source repository, select it, scan it", app_js)
        self.assertIn("Channel actions only create approval records; will_send remains false.", app_js)
        self.assertIn("Document parsing may create candidates, but memory still requires owner review.", app_js)
        self.assertIn('renderProductError("demo-flow")', app_js)
        self.assertIn('renderProductError("channel")', app_js)
        self.assertIn('renderProductError("codegraph-query")', app_js)
        self.assertIn(".product-error", styles)
        self.assertIn(".error-guide-grid", styles)

    def test_quickstart_and_deploy_docs_reference_console_demo_flow_and_readiness(self):
        readme = Path("README.md").read_text(encoding="utf-8")
        deployment = Path("docs/12-one-click-deployment.md").read_text(encoding="utf-8")
        deploy_ps1 = Path("scripts/deploy-usable.ps1").read_text(encoding="utf-8")
        deploy_sh = Path("scripts/deploy-usable.sh").read_text(encoding="utf-8")
        env_example = Path(".env.example").read_text(encoding="utf-8")
        compose = Path("docker-compose.production.yml").read_text(encoding="utf-8")
        server_env = Path("infra/hermes/env.example").read_text(encoding="utf-8")

        combined_docs = readme + "\n" + deployment
        self.assertIn("python -m src.hermes demo flow", combined_docs)
        self.assertIn("http://127.0.0.1:8787/console", combined_docs)
        self.assertIn("endpoints.demo_flow", deployment)
        self.assertIn("no_external_send", deployment)
        self.assertIn("no_auto_memory_write", deployment)
        self.assertIn("Set-EnvValue \"POSTGRES_DB\" \"bairui\"", deploy_ps1)
        self.assertIn('set_env_value "POSTGRES_DB" "bairui"', deploy_sh)
        self.assertIn("/demo/flow", deploy_ps1)
        self.assertIn("/demo/flow", deploy_sh)
        self.assertIn("/console", deploy_ps1)
        self.assertIn("/console", deploy_sh)
        self.assertIn("POSTGRES_DB=bairui", env_example)
        self.assertIn("POSTGRES_USER=bairui", env_example)
        self.assertIn("container_name: bairui-postgres", compose)
        self.assertIn("container_name: bairui-runtime", compose)
        self.assertIn("postgresql://bairui:", server_env)

    def test_avatar_engine_status_uses_advanced_runtime_contract(self):
        state = avatar_engine_status(load_settings())
        self.assertEqual(state.package, "pixi-live2d-display-advanced")
        self.assertEqual(state.license, "MIT")
        self.assertIn("audio_lipsync", state.supports)
        self.assertIn("npm install pixi-live2d-display-advanced", state.install_hint)

    def test_avatar_manifest_defaults_to_browser_renderer(self):
        manifest = build_avatar_manifest(load_settings())
        self.assertEqual(manifest["brand"], "bairui")
        self.assertEqual(manifest["engine"]["package"], "pixi-live2d-display-advanced")
        self.assertEqual(manifest["runtime"]["renderer"], "browser")
        self.assertFalse(manifest["runtime"]["backend_renders_live2d"])
        self.assertIn("speaking", manifest["state_map"])

    def test_avatar_validation_accepts_model3_manifest_with_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model_dir = root / "avatar"
            model_dir.mkdir()
            (model_dir / "model.moc3").write_bytes(b"moc")
            (model_dir / "texture.png").write_bytes(b"png")
            (model_dir / "idle.motion3.json").write_text("{}", encoding="utf-8")
            (model_dir / "happy.exp3.json").write_text("{}", encoding="utf-8")
            manifest_path = model_dir / "bairui.model3.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "FileReferences": {
                            "Moc": "model.moc3",
                            "Textures": ["texture.png"],
                            "Motions": {"idle": [{"File": "idle.motion3.json"}]},
                            "Expressions": [{"Name": "happy", "File": "happy.exp3.json"}],
                        }
                    }
                ),
                encoding="utf-8",
            )
            env = {
                "HERMES_DATA_DIR": str(root / "data"),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
                "BAIRUI_AVATAR_ASSETS_DIR": str(root),
                "BAIRUI_AVATAR_DEFAULT_MODEL": "avatar/bairui.model3.json",
            }
            with patch.dict(os.environ, env, clear=False):
                settings = load_settings()
                validation = validate_avatar_model(settings, "avatar/bairui.model3.json")
                manifest = build_avatar_manifest(settings)
        self.assertEqual(validation.status, "valid")
        self.assertEqual(validation.model_format, "model3")
        self.assertEqual(validation.missing_files, ())
        self.assertTrue(manifest["model"]["configured"])
        self.assertEqual(manifest["model"]["url"], "/avatars/assets/avatar/bairui.model3.json")

    def test_avatar_validation_reports_missing_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = root / "broken.model3.json"
            manifest_path.write_text(
                json.dumps({"FileReferences": {"Moc": "missing.moc3", "Textures": ["missing.png"]}}),
                encoding="utf-8",
            )
            env = {
                "HERMES_DATA_DIR": str(root / "data"),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
                "BAIRUI_AVATAR_ASSETS_DIR": str(root),
            }
            with patch.dict(os.environ, env, clear=False):
                validation = validate_avatar_model(load_settings(), "broken.model3.json")
        self.assertEqual(validation.status, "missing_assets")
        self.assertIn("missing.moc3", validation.missing_files)
        self.assertIn("missing.png", validation.missing_files)

    def test_avatar_state_change_is_audited(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = {
                "HERMES_DATA_DIR": str(root / "data"),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
            }
            with patch.dict(os.environ, env, clear=False):
                settings = load_settings()
                result = set_avatar_state(settings, {"state": "speaking", "text": "hello", "audio_url": "/tts/1.wav"})
                audit = list_audit_events(settings.data_dir)
        self.assertEqual(result["status"], "accepted")
        self.assertTrue(result["lip_sync"])
        self.assertEqual(audit[-1]["action"], "avatar.state_changed")
        self.assertEqual(audit[-1]["resource_type"], "avatar")

    def test_avatar_state_rejects_unknown_state(self):
        result = set_avatar_state(load_settings(), {"state": "dancing"})
        self.assertEqual(result["status"], "invalid_state")
        self.assertIn("idle", result["allowed_states"])

    def test_cli_avatar_status_prints_advanced_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "HERMES_DATA_DIR": str(Path(tmp) / "data"),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
            }
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.cli.print_json") as print_json:
                    code = run(["avatar", "status"])
        self.assertEqual(code, 0)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["service"], "bairui")
        self.assertEqual(payload["avatar"]["package"], "pixi-live2d-display-advanced")

    def test_cli_avatar_state_records_state_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = {
                "HERMES_DATA_DIR": str(root / "data"),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
            }
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.cli.print_json") as print_json:
                    code = run(["avatar", "state", "--state", "speaking", "--text", "ready"])
        self.assertEqual(code, 0)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["avatar_state"]["status"], "accepted")
        self.assertEqual(payload["avatar_state"]["state"], "speaking")

    def test_public_api_service_name_is_bairui(self):
        self.assertEqual(PUBLIC_SERVICE, "bairui")

    def test_create_job_writes_job_and_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            job = create_job(data_dir, title="First job", prompt="Summarize this", route="research")
            self.assertEqual(job.status, "queued")
            self.assertEqual(len(list_jobs(data_dir)), 1)
            audit = list_audit_events(data_dir)
            self.assertEqual(audit[0]["action"], "job.created")

    def test_frontend_events_project_audit_for_sse(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            create_job(data_dir, title="First job", prompt="Summarize this", route="research")
            events = list_frontend_events(data_dir)
            self.assertEqual(events[0]["type"], "job.created")
            self.assertEqual(events[0]["data"]["action"], "job.created")
            self.assertEqual(events[0]["data"]["resource_type"], "job")
            frame = build_sse_frame(events[0]).decode("utf-8")
            self.assertIn("event: job.created", frame)
            self.assertIn('"type": "job.created"', frame)

    def test_frontend_event_falls_back_to_audit_event(self):
        event = audit_event_to_frontend_event(
            {
                "id": "evt_1",
                "action": "unknown.action",
                "resource_type": "runtime",
                "resource_ref": "local",
                "risk_level": "low",
                "payload": {"ok": True},
                "created_at": "2026-06-11T00:00:00+00:00",
            }
        )
        self.assertEqual(event["type"], "audit.event")
        self.assertEqual(event["data"]["payload"], {"ok": True})

    def test_channels_default_status_requires_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "HERMES_DATA_DIR": str(Path(tmp) / "data"),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
                "BAIRUI_CHANNELS_ENABLED": "",
            }
            with patch.dict(os.environ, env, clear=False):
                settings = load_settings()
                status = channel_status(settings)
                targets = channel_targets(settings)
        self.assertEqual(status.status, "missing_config")
        self.assertIn("channels_disabled", status.blockers)
        self.assertEqual(targets[0]["id"], "owner_review")
        self.assertEqual(targets[0]["channel_type"], "personal_chat")

    def test_channel_target_diagnostics_explain_disabled_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "HERMES_DATA_DIR": str(Path(tmp) / "data"),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
                "BAIRUI_CHANNELS_ENABLED": "",
            }
            with patch.dict(os.environ, env, clear=False):
                diagnostics = diagnose_channel_targets(load_settings())
        self.assertEqual(diagnostics[0].id, "owner_review")
        self.assertEqual(diagnostics[0].status, "missing_config")
        self.assertIn("channels_disabled", diagnostics[0].blockers)
        self.assertEqual(diagnostics[0].supports, ("text", "image", "video", "file"))

    def test_channel_target_diagnostics_support_configured_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "HERMES_DATA_DIR": str(Path(tmp) / "data"),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
                "BAIRUI_CHANNELS_ENABLED": "1",
                "BAIRUI_CHANNEL_TARGETS_JSON": json.dumps(
                    [
                        {
                            "id": "ops_review",
                            "label": "Ops Review",
                            "channel_type": "team_webhook",
                            "supports": ["text", "file"],
                        }
                    ]
                ),
            }
            with patch.dict(os.environ, env, clear=False):
                diagnostics = diagnose_channel_targets(load_settings())
        self.assertEqual(diagnostics[0].id, "ops_review")
        self.assertEqual(diagnostics[0].status, "approval_required")
        self.assertEqual(diagnostics[0].supports, ("text", "file"))
        self.assertEqual(diagnostics[0].blockers, ())

    def test_channel_send_plan_is_audited_and_never_sends(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            env = {
                "HERMES_DATA_DIR": str(data_dir),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
                "BAIRUI_CHANNELS_ENABLED": "1",
            }
            with patch.dict(os.environ, env, clear=False):
                result = plan_channel_send(
                    load_settings(),
                    {"target_id": "owner_review", "text": "approve this summary", "media_kind": "text"},
                )
                audit = list_audit_events(data_dir)
                requests = list_channel_approval_requests(data_dir)
        self.assertEqual(result.status, "approval_required")
        self.assertFalse(result.will_send)
        self.assertEqual(result.reason, "owner_confirmation_required")
        self.assertEqual(audit[-1]["action"], "channel.send_planned")
        self.assertEqual(audit[-1]["payload"]["will_send"], False)
        self.assertEqual(requests[-1]["status"], "pending_review")
        self.assertEqual(result.approval_request_id, requests[-1]["id"])

    def test_channel_approvals_list_and_review_do_not_send(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            env = {
                "HERMES_DATA_DIR": str(data_dir),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
                "BAIRUI_CHANNELS_ENABLED": "1",
            }
            with patch.dict(os.environ, env, clear=False):
                settings = load_settings()
                plan = plan_channel_send(
                    settings,
                    {"target_id": "owner_review", "text": "approval queue item", "media_kind": "text"},
                )
                approvals = list_channel_approvals(settings, only_pending=True)
                review = review_channel_approval(
                    settings,
                    {"request_id": plan.approval_request_id, "decision": "approve", "reviewer_ref": "owner", "note": "ok"},
                )
                after_review = list_channel_approvals(settings, only_pending=True)
                reviews = list_channel_approval_reviews(data_dir)
        self.assertEqual(len(approvals), 1)
        self.assertEqual(approvals[0]["review_status"], "pending_review")
        self.assertEqual(review.status, "reviewed")
        self.assertFalse(review.will_send)
        self.assertEqual(review.reason, "review_recorded_without_external_dispatch")
        self.assertEqual(after_review, ())
        self.assertEqual(reviews[-1]["decision"], "approve")
        self.assertEqual(reviews[-1]["will_send"], False)

    def test_channel_approval_reviews_http_endpoint_lists_review_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "HERMES_DATA_DIR": str(Path(tmp) / "data"),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
                "BAIRUI_CHANNELS_ENABLED": "1",
            }
            with patch.dict(os.environ, env, clear=False):
                server = ThreadingHTTPServer(("127.0.0.1", 0), HermesHandler)
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    plan_status, _, plan_body = _http_post(
                        server.server_port,
                        "/channels/send",
                        {"target_id": "owner_review", "text": "review endpoint item", "media_kind": "text"},
                    )
                    request_id = json.loads(plan_body.decode("utf-8"))["channel_send"]["approval_request_id"]
                    review_status, _, review_body = _http_post(
                        server.server_port,
                        "/channels/approvals/review",
                        {"request_id": request_id, "decision": "reject", "reviewer_ref": "owner", "note": "test"},
                    )
                    reviews_status, _, reviews_body = _http_get(server.server_port, "/channels/approvals/reviews")
                    reviews = json.loads(reviews_body.decode("utf-8"))["channel_approval_reviews"]
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join(timeout=2)

        self.assertEqual(plan_status, 202)
        self.assertEqual(review_status, 200)
        self.assertEqual(reviews_status, 200)
        self.assertEqual(reviews[-1]["request_id"], request_id)
        self.assertEqual(reviews[-1]["decision"], "reject")
        self.assertFalse(reviews[-1]["will_send"])

    def test_channel_approval_review_rejects_duplicate_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "HERMES_DATA_DIR": str(Path(tmp) / "data"),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
                "BAIRUI_CHANNELS_ENABLED": "1",
            }
            with patch.dict(os.environ, env, clear=False):
                settings = load_settings()
                plan = plan_channel_send(
                    settings,
                    {"target_id": "owner_review", "text": "duplicate review item", "media_kind": "text"},
                )
                first = review_channel_approval(settings, {"request_id": plan.approval_request_id, "decision": "reject"})
                second = review_channel_approval(settings, {"request_id": plan.approval_request_id, "decision": "approve"})
        self.assertEqual(first.status, "reviewed")
        self.assertEqual(second.status, "already_reviewed")

    def test_frontend_events_project_channel_send_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            env = {
                "HERMES_DATA_DIR": str(data_dir),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
                "BAIRUI_CHANNELS_ENABLED": "1",
            }
            with patch.dict(os.environ, env, clear=False):
                plan_channel_send(
                    load_settings(),
                    {"target_id": "owner_review", "text": "approve this summary", "media_kind": "text"},
                )
                events = list_frontend_events(data_dir)
        self.assertEqual(events[-1]["type"], "channel.send.approval_required")
        self.assertEqual(events[-1]["data"]["action"], "channel.send_planned")
        self.assertEqual(events[-1]["data"]["resource_type"], "channel_target")
        self.assertFalse(events[-1]["data"]["payload"]["will_send"])

    def test_channel_send_rejects_unsupported_media(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "HERMES_DATA_DIR": str(Path(tmp) / "data"),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
                "BAIRUI_CHANNELS_ENABLED": "1",
            }
            with patch.dict(os.environ, env, clear=False):
                result = plan_channel_send(
                    load_settings(),
                    {"target_id": "owner_review", "text": "hello", "media_kind": "audio"},
                )
        self.assertEqual(result.status, "unsupported_media")
        self.assertEqual(result.reason, "unsupported_media_kind")

    def test_frontend_events_project_blocked_channel_send(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            env = {
                "HERMES_DATA_DIR": str(data_dir),
                "HERMES_LOG_DIR": str(Path(tmp) / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(Path(tmp) / "vault"),
                "BAIRUI_CHANNELS_ENABLED": "",
            }
            with patch.dict(os.environ, env, clear=False):
                plan_channel_send(
                    load_settings(),
                    {"target_id": "owner_review", "text": "blocked by default", "media_kind": "text"},
                )
                events = list_frontend_events(data_dir)
        self.assertEqual(events[-1]["type"], "channel.send.blocked")
        self.assertEqual(events[-1]["data"]["action"], "channel.send_blocked")
        self.assertEqual(events[-1]["data"]["payload"]["reason"], "channels_disabled")

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

    def test_review_document_memory_candidate_rejects_and_writes_obsidian_graph_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            (output_dir / "sample.md").write_text(
                "Bairui Hermes document memory candidates must be reviewed before EverOS promotion.",
                encoding="utf-8",
            )
            ingest = create_document_ingest(
                data_dir,
                title="Review plan",
                input_path="sample.pdf",
                output_dir=str(output_dir),
                parser_command=("mineru", "-p", "sample.pdf", "-o", str(output_dir)),
            )
            register_document_artifacts(data_dir, ingest.id)
            candidate = generate_document_memory_candidates(data_dir, ingest.id).candidates[0]
            env = {
                "HERMES_DATA_DIR": str(data_dir),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
                "EVEROS_BASE_URL": "",
            }
            with patch.dict(os.environ, env, clear=False):
                result = review_document_memory_candidate(load_settings(), candidate.id, decision="reject", note="not durable")
            reviews = list_document_memory_reviews(data_dir)
            note_path = Path(result.obsidian_note["path"])
            note_exists = note_path.exists()
            note_text = note_path.read_text(encoding="utf-8")
            moc_path = root / "vault" / "00-Inbox" / "everos-candidates" / "Document Memory Candidates.md"
            moc_exists = moc_path.exists()
        self.assertEqual(result.status, "rejected")
        self.assertEqual(result.review.status, "rejected")
        self.assertEqual(reviews[0]["decision"], "reject")
        self.assertTrue(note_exists)
        self.assertTrue(moc_exists)
        self.assertIn("[[Document Memory Candidates]]", note_text)
        self.assertIn("[[Bairui]]", note_text)
        self.assertIn("[[Hermes]]", note_text)
        self.assertIn("[[EverOS]]", note_text)
        self.assertIn("Bairui Hermes document memory candidates", note_text)

    def test_review_document_memory_candidate_approve_records_missing_everos_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            (output_dir / "sample.md").write_text(
                "Bairui Hermes keeps reviewed project requirements in EverOS after owner approval.",
                encoding="utf-8",
            )
            ingest = create_document_ingest(
                data_dir,
                title="Missing EverOS plan",
                input_path="sample.pdf",
                output_dir=str(output_dir),
                parser_command=("mineru", "-p", "sample.pdf", "-o", str(output_dir)),
            )
            register_document_artifacts(data_dir, ingest.id)
            candidate = generate_document_memory_candidates(data_dir, ingest.id).candidates[0]
            env = {
                "HERMES_DATA_DIR": str(data_dir),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
                "EVEROS_BASE_URL": "",
            }
            with patch.dict(os.environ, env, clear=False):
                result = review_document_memory_candidate(load_settings(), candidate.id, decision="approve")
            note_text = Path(result.obsidian_note["path"]).read_text(encoding="utf-8")
        self.assertEqual(result.status, "promotion_failed")
        self.assertEqual(result.review.everos_status, "missing_config")
        self.assertIn("promotion_failed", note_text)
        self.assertIn("[[EverOS]]", note_text)

    def test_review_document_memory_candidate_approve_promotes_to_everos(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            (output_dir / "sample.md").write_text(
                "Bairui Hermes product memory should persist approved commercial requirements.",
                encoding="utf-8",
            )
            ingest = create_document_ingest(
                data_dir,
                title="Approve plan",
                input_path="sample.pdf",
                output_dir=str(output_dir),
                parser_command=("mineru", "-p", "sample.pdf", "-o", str(output_dir)),
            )
            register_document_artifacts(data_dir, ingest.id)
            candidate = generate_document_memory_candidates(data_dir, ingest.id).candidates[0]
            env = {
                "HERMES_DATA_DIR": str(data_dir),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
                "EVEROS_BASE_URL": "http://127.0.0.1:9999",
            }
            everos_result = EverOSResult(status="completed", endpoint="/api/v1/memory/add", payload={}, response={"ok": True})
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.document_pipeline.everos_add_memory", return_value=everos_result) as add_memory:
                    result = review_document_memory_candidate(load_settings(), candidate.id, decision="approve", user_id="owner")
            payload = add_memory.call_args.args[1]
        self.assertEqual(result.status, "approved")
        self.assertEqual(result.review.everos_status, "completed")
        self.assertEqual(add_memory.call_count, 1)
        self.assertIn("approved commercial requirements", payload["messages"][0]["content"])

    def test_review_document_memory_candidate_blocks_duplicate_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            (output_dir / "sample.md").write_text(
                "Bairui Hermes owner rules become memory only after review.",
                encoding="utf-8",
            )
            ingest = create_document_ingest(
                data_dir,
                title="Duplicate review plan",
                input_path="sample.pdf",
                output_dir=str(output_dir),
                parser_command=("mineru", "-p", "sample.pdf", "-o", str(output_dir)),
            )
            register_document_artifacts(data_dir, ingest.id)
            candidate = generate_document_memory_candidates(data_dir, ingest.id).candidates[0]
            env = {
                "HERMES_DATA_DIR": str(data_dir),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
            }
            with patch.dict(os.environ, env, clear=False):
                first = review_document_memory_candidate(load_settings(), candidate.id, decision="reject")
                second = review_document_memory_candidate(load_settings(), candidate.id, decision="reject")
        self.assertEqual(first.status, "rejected")
        self.assertEqual(second.status, "already_reviewed")

    def test_document_memory_review_queue_and_batch_reject_pending_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            (output_dir / "sample.md").write_text(
                "Owner preference: Hermes should keep durable requirements only after explicit review.\n\n"
                "Bairui Hermes project rule: batch review must still write Obsidian graph notes.",
                encoding="utf-8",
            )
            ingest = create_document_ingest(
                data_dir,
                title="Batch review plan",
                input_path="sample.pdf",
                output_dir=str(output_dir),
                parser_command=("python", "-c", "print('batch review parse ok')"),
            )
            run_document_ingest(data_dir, ingest.id, timeout_seconds=10)
            register_document_artifacts(data_dir, ingest.id)
            generate_document_memory_candidates(data_dir, ingest.id, max_candidates=2)
            env = {
                "HERMES_DATA_DIR": str(data_dir),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
                "SONIC_HOST": "127.0.0.1",
                "SONIC_PASSWORD": "secret",
            }
            sonic_result = SonicResult(status="completed", channel="ingest", command="PUSH", payload={})
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.document_pipeline.sonic_push", return_value=sonic_result):
                    queue = list_pending_document_memory_reviews(load_settings(), ingest_id=ingest.id)
                    result = review_document_memory_candidates_batch(
                        load_settings(),
                        tuple(candidate["id"] for candidate in queue.candidates),
                        decision="reject",
                        note="batch reviewed",
                        resume_after_review=True,
                        timeout_seconds=10,
                    )
                    refreshed = list_pending_document_memory_reviews(load_settings(), ingest_id=ingest.id)
            notes_dir = root / "vault" / "00-Inbox" / "everos-candidates"
            note_count = len(list(notes_dir.glob("*.md"))) - 1
        self.assertEqual(queue.status, "ready")
        self.assertEqual(queue.pending_count, 2)
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.reviewed_count, 2)
        self.assertEqual(result.skipped_count, 0)
        self.assertIsNotNone(result.state)
        self.assertEqual(result.state.pipeline["memory_reviews"], "completed")
        self.assertEqual(result.state.pipeline["source_refs"], "completed")
        self.assertEqual(result.state.pipeline["obsidian_report"], "completed")
        self.assertIsNotNone(result.workbench_run)
        self.assertEqual(result.workbench_run.status, "completed")
        self.assertEqual(refreshed.pending_count, 0)
        self.assertEqual(refreshed.reviewed_count, 2)
        self.assertEqual(note_count, 2)

    def test_create_document_source_refs_links_artifacts_index_and_memory_reviews(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            (output_dir / "sample.md").write_text(
                "Bairui Hermes source references connect document artifacts, Sonic index runs, and EverOS reviews.",
                encoding="utf-8",
            )
            ingest = create_document_ingest(
                data_dir,
                title="Source refs plan",
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
                index_document_artifacts(load_settings(), ingest.id)
                candidate = generate_document_memory_candidates(data_dir, ingest.id).candidates[0]
                review_document_memory_candidate(load_settings(), candidate.id, decision="reject")
                result = create_document_source_refs(load_settings(), ingest.id)
            refs = list_source_refs(data_dir, limit=20)
            source_types = {ref["source_type"] for ref in refs}
        self.assertEqual(result.status, "completed")
        self.assertIn("document_artifact", source_types)
        self.assertIn("document_index_run", source_types)
        self.assertIn("document_memory_candidate", source_types)
        memory_ref = next(ref for ref in refs if ref["source_type"] == "document_memory_candidate")
        self.assertEqual(memory_ref["metadata"]["review_status"], "rejected")
        self.assertEqual(memory_ref["provider"], "hermes")

    def test_create_document_ingest_report_writes_obsidian_graph_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            (output_dir / "sample.md").write_text(
                "Bairui Hermes ingest reports should summarize artifacts, Sonic indexing, memory review, and source refs.",
                encoding="utf-8",
            )
            ingest = create_document_ingest(
                data_dir,
                title="Report plan",
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
                index_document_artifacts(load_settings(), ingest.id)
                candidate = generate_document_memory_candidates(data_dir, ingest.id).candidates[0]
                review_document_memory_candidate(load_settings(), candidate.id, decision="reject")
                create_document_source_refs(load_settings(), ingest.id)
                result = create_document_ingest_report(load_settings(), ingest.id)
            reports = list_document_ingest_reports(data_dir)
            report_path = Path(result.report.path)
            report_exists = report_path.exists()
            report_text = report_path.read_text(encoding="utf-8")
            moc_path = root / "vault" / "05_Reports" / "document-ingests" / "Document Ingest Reports.md"
            moc_exists = moc_path.exists()
        self.assertEqual(result.status, "completed")
        self.assertEqual(reports[0]["ingest_id"], ingest.id)
        self.assertTrue(report_exists)
        self.assertTrue(moc_exists)
        self.assertIn("[[Document Ingest Reports]]", report_text)
        self.assertIn("[[Document Memory Candidates]]", report_text)
        self.assertIn("[[MinerU]]", report_text)
        self.assertIn("[[Sonic]]", report_text)
        self.assertIn("[[EverOS]]", report_text)
        self.assertIn("Memory Candidates And Reviews", report_text)
        self.assertIn("Source References", report_text)

    def test_document_workbench_state_summarizes_ingest_pipeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            (output_dir / "sample.md").write_text(
                "Bairui Hermes workbench state should summarize artifacts, reviews, source refs, and reports.",
                encoding="utf-8",
            )
            ingest = create_document_ingest(
                data_dir,
                title="Workbench plan",
                input_path="sample.pdf",
                output_dir=str(output_dir),
                parser_command=("python", "-c", "print('workbench parser ok')"),
            )
            run_document_ingest(data_dir, ingest.id, timeout_seconds=10)
            register_document_artifacts(data_dir, ingest.id)
            env = {
                "HERMES_DATA_DIR": str(data_dir),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
                "SONIC_HOST": "",
                "SONIC_PASSWORD": "",
            }
            with patch.dict(os.environ, env, clear=False):
                index_document_artifacts(load_settings(), ingest.id)
                candidate = generate_document_memory_candidates(data_dir, ingest.id).candidates[0]
                review_document_memory_candidate(load_settings(), candidate.id, decision="reject")
                create_document_source_refs(load_settings(), ingest.id)
                create_document_ingest_report(load_settings(), ingest.id)
                state = build_document_workbench_state(load_settings(), ingest.id)
        self.assertEqual(state.status, "partial")
        self.assertEqual(state.pipeline["artifact_registration"], "completed")
        self.assertEqual(state.pipeline["memory_reviews"], "completed")
        self.assertEqual(state.pipeline["source_refs"], "completed")
        self.assertEqual(state.pipeline["obsidian_report"], "completed")
        self.assertEqual(state.counts["artifacts"], 1)
        self.assertEqual(state.counts["memory_reviews"], 1)
        self.assertEqual(state.next_actions[0]["command"], "done")
        self.assertFalse(state.blockers)
        self.assertTrue(any("Sonic index" in warning for warning in state.warnings))

    def test_document_ingest_session_summary_is_frontend_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            (output_dir / "sample.md").write_text(
                "Owner preference: session summary should show reviewed memory and generated report.",
                encoding="utf-8",
            )
            ingest = create_document_ingest(
                data_dir,
                title="Session summary plan",
                input_path="sample.pdf",
                output_dir=str(output_dir),
                parser_command=("python", "-c", "print('session summary parse ok')"),
            )
            run_document_ingest(data_dir, ingest.id, timeout_seconds=10)
            register_document_artifacts(data_dir, ingest.id)
            env = {
                "HERMES_DATA_DIR": str(data_dir),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
                "SONIC_HOST": "127.0.0.1",
                "SONIC_PASSWORD": "secret",
            }
            sonic_result = SonicResult(status="completed", channel="ingest", command="PUSH", payload={})
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.document_pipeline.sonic_push", return_value=sonic_result):
                    index_document_artifacts(load_settings(), ingest.id)
                    candidate = generate_document_memory_candidates(data_dir, ingest.id).candidates[0]
                    review_document_memory_candidate(load_settings(), candidate.id, decision="reject")
                    create_document_source_refs(load_settings(), ingest.id)
                    create_document_ingest_report(load_settings(), ingest.id)
                    summary = build_document_ingest_session_summary(load_settings(), ingest.id)
        self.assertEqual(summary.status, "ready")
        self.assertEqual(summary.current_stage, "done")
        self.assertEqual(summary.progress_percent, 100)
        self.assertEqual(summary.primary_action["command"], "done")
        self.assertEqual(summary.review_queue.pending_count, 0)
        self.assertEqual(summary.report["ingest_id"], ingest.id)
        self.assertEqual(summary.stages[-1]["id"], "obsidian_report")

    def test_document_ingest_session_list_is_frontend_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            planned = create_document_ingest(
                data_dir,
                title="Planned list row",
                input_path="planned.pdf",
                output_dir=str(output_dir),
                parser_command=("mineru", "-p", "planned.pdf", "-o", str(output_dir)),
            )
            parsed = create_document_ingest(
                data_dir,
                title="Parsed list row",
                input_path="parsed.pdf",
                output_dir=str(output_dir),
                parser_command=("python", "-c", "print('parsed list row')"),
            )
            run_document_ingest(data_dir, parsed.id, timeout_seconds=10)
            env = {
                "HERMES_DATA_DIR": str(data_dir),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
            }
            with patch.dict(os.environ, env, clear=False):
                sessions = list_document_ingest_session_summaries(load_settings(), limit=10)
        self.assertEqual(sessions.status, "completed")
        self.assertEqual(sessions.count, 2)
        self.assertEqual(sessions.sessions[0].ingest_id, planned.id)
        self.assertEqual(sessions.sessions[0].current_stage, "parse")
        self.assertEqual(sessions.sessions[0].primary_action["command"], "run-ingest")
        self.assertEqual(sessions.sessions[1].ingest_id, parsed.id)
        self.assertEqual(sessions.sessions[1].current_stage, "artifact_registration")
        self.assertEqual(sessions.sessions[1].primary_action["command"], "register-artifacts")
        self.assertEqual(sessions.sessions[1].pending_reviews, 0)

    def test_document_workbench_next_executes_parser_step(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            ingest = create_document_ingest(
                data_dir,
                title="Workbench next plan",
                input_path="sample.pdf",
                output_dir=str(output_dir),
                parser_command=("python", "-c", "print('workbench next ok')"),
            )
            env = {
                "HERMES_DATA_DIR": str(data_dir),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
            }
            with patch.dict(os.environ, env, clear=False):
                result = execute_document_workbench_next(load_settings(), ingest.id, timeout_seconds=10)
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.action["command"], "run-ingest")
        self.assertEqual(result.result.status, "completed")
        self.assertEqual(result.state.pipeline["parse"], "completed")

    def test_document_workbench_next_stops_for_memory_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            (output_dir / "sample.md").write_text("Owner must review this memory candidate.", encoding="utf-8")
            ingest = create_document_ingest(
                data_dir,
                title="Review stop plan",
                input_path="sample.pdf",
                output_dir=str(output_dir),
                parser_command=("python", "-c", "print('ok')"),
            )
            run_document_ingest(data_dir, ingest.id, timeout_seconds=10)
            register_document_artifacts(data_dir, ingest.id)
            env = {
                "HERMES_DATA_DIR": str(data_dir),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
                "SONIC_HOST": "",
                "SONIC_PASSWORD": "",
            }
            with patch.dict(os.environ, env, clear=False):
                index_document_artifacts(load_settings(), ingest.id)
                generate_document_memory_candidates(data_dir, ingest.id)
                result = execute_document_workbench_next(load_settings(), ingest.id, timeout_seconds=10)
        self.assertEqual(result.status, "needs_review")
        self.assertEqual(result.action["command"], "review-memory-candidate")
        self.assertEqual(len(result.result["pending_candidates"]), 1)
        self.assertEqual(result.state.counts["memory_reviews"], 0)

    def test_document_workbench_run_until_blocked_stops_for_memory_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            (output_dir / "sample.md").write_text("Owner must review this candidate before memory promotion.", encoding="utf-8")
            ingest = create_document_ingest(
                data_dir,
                title="Run until review plan",
                input_path="sample.pdf",
                output_dir=str(output_dir),
                parser_command=("python", "-c", "print('run until blocked ok')"),
            )
            env = {
                "HERMES_DATA_DIR": str(data_dir),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
                "SONIC_HOST": "127.0.0.1",
                "SONIC_PASSWORD": "secret",
            }
            sonic_result = SonicResult(status="completed", channel="ingest", command="PUSH", payload={})
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.document_pipeline.sonic_push", return_value=sonic_result):
                    result = run_document_workbench_until_blocked(load_settings(), ingest.id, timeout_seconds=10)
        self.assertEqual(result.status, "needs_review")
        self.assertEqual([step.action["command"] for step in result.steps], ["run-ingest", "register-artifacts", "index-artifacts", "memory-candidates", "review-memory-candidate"])
        self.assertEqual(result.state.pipeline["parse"], "completed")
        self.assertEqual(result.state.pipeline["artifact_registration"], "completed")
        self.assertEqual(result.state.counts["memory_candidates"], 1)
        self.assertEqual(result.state.counts["memory_reviews"], 0)

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

    def test_postgresql_schema_includes_source_refs(self):
        self.assertIn("create table if not exists source_refs", SCHEMA_SQL)
        self.assertIn("source_type text not null", SCHEMA_SQL)
        self.assertIn("metadata jsonb not null", SCHEMA_SQL)
        self.assertIn("idx_source_refs_source", SCHEMA_SQL)

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
        self.assertIn("frontend-contract", help_text)
        self.assertIn("heartbeat", help_text)
        self.assertIn("memory", help_text)
        self.assertIn("voice", help_text)
        self.assertIn("document", help_text)
        self.assertIn("intel", help_text)
        self.assertIn("simulation", help_text)
        self.assertIn("search", help_text)
        self.assertIn("index", help_text)
        self.assertIn("runtime-readiness", help_text)

    def test_cli_frontend_contract_prints_product_contract(self):
        with patch("src.hermes.cli.print_json") as print_json:
            code = run(["frontend-contract"])
        self.assertEqual(code, 0)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["service"], "bairui")
        contract = payload["frontend_contract"]
        screens = {screen["id"] for screen in contract["screens"]}
        self.assertEqual(contract["service"], "bairui")
        self.assertEqual(contract["product"]["brand_key"], "bairui")
        self.assertIn("activation", screens)
        self.assertIn("document_ingest", screens)
        self.assertIn("runtime_settings", screens)

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
        self.assertEqual(payload["service"], "bairui")
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
        self.assertEqual(payload["service"], "bairui")
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

    def test_cli_document_memory_review_lists_review_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            (output_dir / "sample.md").write_text(
                "Bairui Hermes document memory review writes Obsidian graph links before customer use.",
                encoding="utf-8",
            )
            ingest = create_document_ingest(
                data_dir,
                title="CLI memory review plan",
                input_path="sample.pdf",
                output_dir=str(output_dir),
                parser_command=("mineru", "-p", "sample.pdf", "-o", str(output_dir)),
            )
            register_document_artifacts(data_dir, ingest.id)
            candidate = generate_document_memory_candidates(data_dir, ingest.id).candidates[0]
            env = {
                "HERMES_DATA_DIR": str(data_dir),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
            }
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.cli.print_json") as print_json:
                    code = run(["document", "parse", "review-memory-candidate", "--candidate-id", candidate.id, "--decision", "reject"])
                with patch("src.hermes.cli.print_json") as list_print_json:
                    list_code = run(["document-memory-reviews"])
        self.assertEqual(code, 0)
        self.assertEqual(list_code, 0)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["document_memory_review"].status, "rejected")
        self.assertEqual(list_print_json.call_args.args[0]["document_memory_reviews"][0]["status"], "rejected")

    def test_cli_document_memory_review_pending_and_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            (output_dir / "sample.md").write_text(
                "Owner preference: CLI pending review should show this candidate.\n\n"
                "Bairui Hermes project rule: CLI batch reject must write review records.",
                encoding="utf-8",
            )
            ingest = create_document_ingest(
                data_dir,
                title="CLI batch review plan",
                input_path="sample.pdf",
                output_dir=str(output_dir),
                parser_command=("python", "-c", "print('cli batch review parse ok')"),
            )
            run_document_ingest(data_dir, ingest.id, timeout_seconds=10)
            register_document_artifacts(data_dir, ingest.id)
            candidates = generate_document_memory_candidates(data_dir, ingest.id, max_candidates=2).candidates
            env = {
                "HERMES_DATA_DIR": str(data_dir),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
                "SONIC_HOST": "127.0.0.1",
                "SONIC_PASSWORD": "secret",
            }
            sonic_result = SonicResult(status="completed", channel="ingest", command="PUSH", payload={})
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.document_pipeline.sonic_push", return_value=sonic_result):
                    with patch("src.hermes.cli.print_json") as queue_print_json:
                        queue_code = run(["document", "parse", "memory-review-pending", "--ingest-id", ingest.id])
                    batch_args = [
                        "document",
                        "parse",
                        "memory-review-batch",
                        "--decision",
                        "reject",
                        "--note",
                        "cli batch",
                        "--resume-after-review",
                        "--timeout-seconds",
                        "10",
                    ]
                    for candidate in candidates:
                        batch_args.extend(["--candidate-id", candidate.id])
                    with patch("src.hermes.cli.print_json") as batch_print_json:
                        batch_code = run(batch_args)
        self.assertEqual(queue_code, 0)
        self.assertEqual(batch_code, 0)
        self.assertEqual(queue_print_json.call_args.args[0]["document_memory_review_queue"].pending_count, 2)
        payload = batch_print_json.call_args.args[0]
        self.assertEqual(payload["document_memory_review_batch"].status, "completed")
        self.assertEqual(payload["document_memory_review_batch"].reviewed_count, 2)
        self.assertEqual(payload["document_memory_review_batch"].workbench_run.status, "completed")
        self.assertEqual(payload["document_memory_review_batch"].state.pipeline["obsidian_report"], "completed")

    def test_cli_document_source_refs_lists_source_refs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            (output_dir / "sample.md").write_text(
                "Bairui Hermes source references make document ingestion traceable.",
                encoding="utf-8",
            )
            ingest = create_document_ingest(
                data_dir,
                title="CLI source refs plan",
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
                    code = run(["document", "parse", "source-refs", "--ingest-id", ingest.id])
                with patch("src.hermes.cli.print_json") as list_print_json:
                    list_code = run(["source-refs"])
        self.assertEqual(code, 0)
        self.assertEqual(list_code, 0)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["document_source_refs"].status, "completed")
        self.assertEqual(list_print_json.call_args.args[0]["source_refs"][0]["source_type"], "document_artifact")

    def test_cli_document_ingest_report_lists_report_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            (output_dir / "sample.md").write_text(
                "Bairui Hermes CLI report should create an Obsidian document ingest report.",
                encoding="utf-8",
            )
            ingest = create_document_ingest(
                data_dir,
                title="CLI ingest report plan",
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
                    code = run(["document", "parse", "ingest-report", "--ingest-id", ingest.id])
                with patch("src.hermes.cli.print_json") as list_print_json:
                    list_code = run(["document-ingest-reports"])
            report_path = Path(print_json.call_args.args[0]["document_ingest_report"].report.path)
            report_exists = report_path.exists()
        self.assertEqual(code, 0)
        self.assertEqual(list_code, 0)
        self.assertTrue(report_exists)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["document_ingest_report"].status, "completed")
        self.assertEqual(list_print_json.call_args.args[0]["document_ingest_reports"][0]["ingest_id"], ingest.id)

    def test_cli_document_workbench_state_summarizes_next_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            ingest = create_document_ingest(
                data_dir,
                title="CLI workbench plan",
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
                    code = run(["document", "parse", "workbench-state", "--ingest-id", ingest.id])
        self.assertEqual(code, 0)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["document_workbench"].pipeline["plan"], "completed")
        self.assertEqual(payload["document_workbench"].next_actions[0]["command"], "run-ingest")

    def test_cli_document_ingest_session_summary_prints_primary_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            ingest = create_document_ingest(
                data_dir,
                title="CLI session summary plan",
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
                    code = run(["document", "parse", "session-summary", "--ingest-id", ingest.id])
        self.assertEqual(code, 0)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["document_ingest_session"].current_stage, "parse")
        self.assertEqual(payload["document_ingest_session"].primary_action["command"], "run-ingest")

    def test_cli_document_ingest_session_list_prints_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            create_document_ingest(
                data_dir,
                title="CLI session list row",
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
                    code = run(["document", "parse", "session-list", "--limit", "10"])
        self.assertEqual(code, 0)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["document_ingest_sessions"].count, 1)
        self.assertEqual(payload["document_ingest_sessions"].sessions[0].current_stage, "parse")
        self.assertEqual(payload["document_ingest_sessions"].sessions[0].primary_action["command"], "run-ingest")

    def test_cli_document_workbench_next_executes_next_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            ingest = create_document_ingest(
                data_dir,
                title="CLI workbench next plan",
                input_path="sample.pdf",
                output_dir=str(output_dir),
                parser_command=("python", "-c", "print('cli workbench next ok')"),
            )
            env = {
                "HERMES_DATA_DIR": str(data_dir),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
            }
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.cli.print_json") as print_json:
                    code = run(["document", "parse", "workbench-next", "--ingest-id", ingest.id, "--timeout-seconds", "10"])
        self.assertEqual(code, 0)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["document_workbench_step"].status, "completed")
        self.assertEqual(payload["document_workbench_step"].action["command"], "run-ingest")
        self.assertEqual(payload["document_workbench_step"].state.pipeline["parse"], "completed")

    def test_cli_document_workbench_run_until_blocked_executes_safe_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            output_dir = root / "mineru-output"
            output_dir.mkdir()
            (output_dir / "sample.md").write_text("Owner preference: CLI run until blocked should stop for review before memory promotion.", encoding="utf-8")
            ingest = create_document_ingest(
                data_dir,
                title="CLI workbench run plan",
                input_path="sample.pdf",
                output_dir=str(output_dir),
                parser_command=("python", "-c", "print('cli run ok')"),
            )
            env = {
                "HERMES_DATA_DIR": str(data_dir),
                "HERMES_LOG_DIR": str(root / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(root / "vault"),
                "SONIC_HOST": "127.0.0.1",
                "SONIC_PASSWORD": "secret",
            }
            sonic_result = SonicResult(status="completed", channel="ingest", command="PUSH", payload={})
            with patch.dict(os.environ, env, clear=False):
                with patch("src.hermes.document_pipeline.sonic_push", return_value=sonic_result):
                    with patch("src.hermes.cli.print_json") as print_json:
                        code = run(["document", "parse", "workbench-run-until-blocked", "--ingest-id", ingest.id, "--timeout-seconds", "10"])
        self.assertEqual(code, 0)
        payload = print_json.call_args.args[0]
        self.assertEqual(payload["document_workbench_run"].status, "needs_review")
        self.assertEqual(payload["document_workbench_run"].steps[-1].action["command"], "review-memory-candidate")

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
        self.assertEqual(payload["service"], "bairui")
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
        self.assertEqual(payload["service"], "bairui")
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
        self.assertEqual(payload["service"], "bairui")
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
        self.assertEqual(payload["service"], "bairui")
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
        self.assertEqual(payload["service"], "bairui")
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
        self.assertEqual(payload["service"], "bairui")
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
