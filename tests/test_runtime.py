from __future__ import annotations

import json
import logging
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen

from hermes_runtime.connector_client import HermesConnectorClient
from hermes_runtime.config import RuntimeConfig, load_config
from hermes_runtime.logging_utils import configure_logging
from hermes_runtime.server import build_server, readiness


def make_config(base: Path, **overrides: object) -> RuntimeConfig:
    values = {
        "app_name": "test-hermes",
        "env": "test",
        "host": "127.0.0.1",
        "port": 0,
        "log_dir": base / "logs",
        "data_dir": base / "data",
        "obsidian_vault_dir": base / "obsidian-vault",
        "safe_mode": True,
        "enable_feishu_smoke": False,
        "search_mode": "external_project",
        "search_project": "trendradar",
        "trendradar_base_url": "",
        "trendradar_mcp_command": "",
        "searxng_base_url": "",
        "ai_provider": "supermoxi",
        "ai_base_url": "https://api.supermoxi.cn",
        "ai_api_key_configured": False,
        "ai_default_model": "",
        "ai_fast_model": "",
        "ai_summary_model": "",
        "ai_reasoning_model": "",
        "ai_vision_model": "",
        "ai_timeout_seconds": 60,
        "wechat_mode": "disabled",
        "wechat_channel": "official_account",
        "wechat_persona_mode": "companion",
        "wechat_proactive_chat": False,
        "wechat_max_daily_proactive_messages": 3,
        "wechat_personal_bridge_enabled": False,
        "wechat_official_app_id_configured": False,
        "wechat_official_app_secret_configured": False,
        "wechat_official_token_configured": False,
        "wechat_official_aes_key_configured": False,
        "wecom_corp_id_configured": False,
        "wecom_agent_id_configured": False,
        "wecom_secret_configured": False,
        "wecom_customer_service_token_configured": False,
        "qq_mode": "disabled",
        "qq_bot_app_id_configured": False,
        "qq_bot_token_configured": False,
        "qq_bot_secret_configured": False,
        "qq_webhook_token_configured": False,
        "sticker_bridge_enabled": False,
        "sticker_default_provider": "metadata_only",
        "sticker_default_style": "kawaii_anime",
        "sticker_api_key_configured": False,
        "sticker_image_generation_enabled": False,
        "sticker_image_generation_base_url": "",
        "sticker_image_generation_model": "",
        "sticker_generation_review_required": True,
        "sticker_runtime_cache_enabled": False,
        "social_quick_ack_delay_ms": 1200,
        "social_fast_reply_target_ms": 5000,
        "slow_task_threshold_ms": 5000,
        "async_task_timeout_seconds": 180,
        "latency_telemetry_enabled": True,
    }
    values.update(overrides)
    return RuntimeConfig(**values)


class RuntimeTests(unittest.TestCase):
    def test_load_config_reads_wechat_flags_without_secret_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            env = {
                "HERMES_DATA_DIR": str(base / "data"),
                "HERMES_LOG_DIR": str(base / "logs"),
                "HERMES_OBSIDIAN_VAULT_DIR": str(base / "obsidian-vault"),
                "HERMES_AI_SUMMARY_MODEL": "5.4",
                "HERMES_WECHAT_MODE": "planned",
                "HERMES_WECHAT_CHANNEL": "wecom_customer_service",
                "HERMES_WECHAT_PERSONA_MODE": "companion",
                "HERMES_WECHAT_PROACTIVE_CHAT": "true",
                "HERMES_WECHAT_MAX_DAILY_PROACTIVE_MESSAGES": "2",
                "HERMES_WECHAT_PERSONAL_BRIDGE_ENABLED": "false",
                "HERMES_WECHAT_OFFICIAL_APP_SECRET": "configured-value",
                "HERMES_WECOM_SECRET": "configured-value",
                "HERMES_QQ_MODE": "planned",
                "HERMES_QQ_BOT_APP_ID": "test-app-id",
                "HERMES_QQ_BOT_TOKEN": "configured-value",
                "HERMES_QQ_BOT_SECRET": "configured-value",
                "HERMES_QQ_WEBHOOK_TOKEN": "configured-value",
                "HERMES_STICKER_BRIDGE_ENABLED": "true",
                "HERMES_STICKER_DEFAULT_PROVIDER": "stipop",
                "HERMES_STICKER_DEFAULT_STYLE": "kawaii_anime",
                "HERMES_STICKER_API_KEY": "configured-value",
                "HERMES_STICKER_IMAGE_GENERATION_ENABLED": "true",
                "HERMES_STICKER_IMAGE_GENERATION_BASE_URL": "https://example.invalid",
                "HERMES_STICKER_IMAGE_GENERATION_MODEL": "image2",
                "HERMES_STICKER_GENERATION_REVIEW_REQUIRED": "true",
                "HERMES_STICKER_RUNTIME_CACHE_ENABLED": "false",
                "HERMES_SOCIAL_QUICK_ACK_DELAY_MS": "900",
                "HERMES_SOCIAL_FAST_REPLY_TARGET_MS": "4500",
                "HERMES_SLOW_TASK_THRESHOLD_MS": "5000",
                "HERMES_ASYNC_TASK_TIMEOUT_SECONDS": "240",
                "HERMES_LATENCY_TELEMETRY_ENABLED": "true",
            }

            with patch.dict("os.environ", env, clear=True):
                config = load_config()

            self.assertEqual(config.wechat_mode, "planned")
            self.assertEqual(config.ai_summary_model, "5.4")
            self.assertEqual(config.wechat_channel, "wecom_customer_service")
            self.assertEqual(config.wechat_persona_mode, "companion")
            self.assertTrue(config.wechat_proactive_chat)
            self.assertEqual(config.wechat_max_daily_proactive_messages, 2)
            self.assertFalse(config.wechat_personal_bridge_enabled)
            self.assertTrue(config.wechat_official_app_secret_configured)
            self.assertTrue(config.wecom_secret_configured)
            self.assertEqual(config.qq_mode, "planned")
            self.assertTrue(config.qq_bot_app_id_configured)
            self.assertTrue(config.qq_bot_token_configured)
            self.assertTrue(config.qq_bot_secret_configured)
            self.assertTrue(config.qq_webhook_token_configured)
            self.assertTrue(config.sticker_bridge_enabled)
            self.assertEqual(config.sticker_default_provider, "stipop")
            self.assertEqual(config.sticker_default_style, "kawaii_anime")
            self.assertTrue(config.sticker_api_key_configured)
            self.assertTrue(config.sticker_image_generation_enabled)
            self.assertEqual(
                config.sticker_image_generation_base_url, "https://example.invalid"
            )
            self.assertEqual(config.sticker_image_generation_model, "image2")
            self.assertTrue(config.sticker_generation_review_required)
            self.assertFalse(config.sticker_runtime_cache_enabled)
            self.assertEqual(config.social_quick_ack_delay_ms, 900)
            self.assertEqual(config.social_fast_reply_target_ms, 4500)
            self.assertEqual(config.slow_task_threshold_ms, 5000)
            self.assertEqual(config.async_task_timeout_seconds, 240)
            self.assertTrue(config.latency_telemetry_enabled)

    def test_readiness_is_ready_after_directories_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = make_config(base)
            config.log_dir.mkdir()
            config.data_dir.mkdir()
            config.obsidian_vault_dir.mkdir()

            result = readiness(config)

            self.assertEqual(result["status"], "ready")
            self.assertTrue(all(result["checks"].values()))

    def test_health_endpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = make_config(base, ai_api_key_configured=True)
            logger = configure_logging(config.log_dir)
            server = build_server(config, logger)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

            try:
                url = f"http://127.0.0.1:{server.server_port}/health"
                for _ in range(20):
                    try:
                        with urlopen(url, timeout=2) as response:
                            payload = json.loads(response.read().decode("utf-8"))
                        break
                    except OSError:
                        time.sleep(0.05)
                else:
                    self.fail("server did not respond")

                self.assertEqual(payload["status"], "ok")
                self.assertEqual(payload["service"], "test-hermes")
                self.assertTrue(payload["safe_mode"])
                self.assertEqual(payload["search"]["mode"], "external_project")
                self.assertEqual(payload["search"]["project"], "trendradar")
                self.assertEqual(payload["ai"]["provider"], "supermoxi")
                self.assertTrue(payload["ai"]["base_url_configured"])
                self.assertTrue(payload["ai"]["api_key_configured"])
                self.assertEqual(payload["wechat"]["mode"], "disabled")
                self.assertEqual(payload["wechat"]["channel"], "official_account")
                self.assertEqual(payload["wechat"]["persona_mode"], "companion")
                self.assertFalse(payload["wechat"]["proactive_chat"])
                self.assertFalse(payload["wechat"]["personal_bridge_enabled"])
                self.assertFalse(
                    payload["wechat"]["official_account"]["app_secret_configured"]
                )
                self.assertFalse(payload["wechat"]["wecom"]["secret_configured"])
                self.assertFalse(payload["stickers"]["bridge_enabled"])
                self.assertEqual(payload["qq"]["mode"], "disabled")
                self.assertFalse(payload["qq"]["official_bot"]["app_id_configured"])
                self.assertFalse(payload["qq"]["official_bot"]["token_configured"])
                self.assertFalse(payload["qq"]["official_bot"]["secret_configured"])
                self.assertFalse(
                    payload["qq"]["official_bot"]["webhook_token_configured"]
                )
                self.assertEqual(payload["stickers"]["default_provider"], "metadata_only")
                self.assertEqual(payload["stickers"]["default_style"], "kawaii_anime")
                self.assertFalse(payload["stickers"]["api_key_configured"])
                self.assertFalse(payload["stickers"]["image_generation_enabled"])
                self.assertFalse(
                    payload["stickers"]["image_generation_base_url_configured"]
                )
                self.assertEqual(payload["stickers"]["image_generation_model"], "")
                self.assertTrue(payload["stickers"]["generation_review_required"])
                self.assertFalse(payload["stickers"]["runtime_cache_enabled"])
                self.assertEqual(payload["performance"]["quick_ack_delay_ms"], 1200)
                self.assertEqual(payload["performance"]["fast_reply_target_ms"], 5000)
                self.assertEqual(payload["performance"]["slow_task_threshold_ms"], 5000)
                self.assertEqual(
                    payload["performance"]["async_task_timeout_seconds"], 180
                )
                self.assertTrue(payload["performance"]["latency_telemetry_enabled"])
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)
                for handler in list(logger.handlers):
                    logger.removeHandler(handler)
                    handler.close()
                logging.shutdown()

    def test_performance_endpoint_exposes_safe_latency_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = make_config(
                base,
                ai_fast_model="5.4-mini",
                ai_summary_model="5.4",
                ai_reasoning_model="5.5",
                ai_vision_model="gpt-5.5-vision",
            )
            logger = configure_logging(config.log_dir)
            server = build_server(config, logger)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

            try:
                url = f"http://127.0.0.1:{server.server_port}/performance"
                with urlopen(url, timeout=2) as response:
                    payload = json.loads(response.read().decode("utf-8"))

                self.assertEqual(payload["status"], "ok")
                self.assertEqual(payload["profile"]["quick_ack_delay_ms"], 1200)
                self.assertEqual(payload["profile"]["fast_reply_target_ms"], 5000)
                self.assertIn("slow_task", payload["latency_budgets"])
                self.assertEqual(payload["routing_slots"]["fast"], "5.4-mini")
                self.assertEqual(payload["routing_slots"]["summary"], "5.4")
                self.assertEqual(payload["routing_slots"]["reasoning"], "5.5")
                self.assertEqual(payload["routing_slots"]["vision"], "gpt-5.5-vision")
                self.assertEqual(payload["route_types"]["image_generate"], "enabled")
                self.assertNotIn("api_key", json.dumps(payload).lower())
                self.assertNotIn("secret", json.dumps(payload).lower())
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)
                for handler in list(logger.handlers):
                    logger.removeHandler(handler)
                    handler.close()
                logging.shutdown()

    def test_capabilities_endpoint_exposes_frontend_health_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = make_config(
                base,
                obsidian_vault_dir=base / "obsidian-vault",
                ai_api_key_configured=True,
                ai_fast_model="5.4-mini",
                ai_summary_model="5.4",
                trendradar_base_url="http://127.0.0.1:3333",
                wechat_mode="planned",
                qq_mode="official_bot",
                qq_bot_app_id_configured=True,
                qq_bot_token_configured=True,
                qq_bot_secret_configured=True,
                qq_webhook_token_configured=True,
                sticker_bridge_enabled=True,
            )
            config.obsidian_vault_dir.mkdir(parents=True)
            logger = configure_logging(config.log_dir)
            server = build_server(config, logger)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

            try:
                url = f"http://127.0.0.1:{server.server_port}/capabilities"
                with urlopen(url, timeout=2) as response:
                    payload = json.loads(response.read().decode("utf-8"))

                self.assertEqual(payload["status"], "ok")
                self.assertEqual(payload["service"], "test-hermes")
                self.assertEqual(payload["capabilities"]["runtime"]["state"], "ready")
                self.assertEqual(
                    payload["capabilities"]["model_gateway"]["state"], "ready"
                )
                self.assertEqual(
                    payload["capabilities"]["search_intelligence"]["state"], "ready"
                )
                self.assertEqual(
                    payload["capabilities"]["memory_governance"]["state"], "ready"
                )
                self.assertEqual(payload["capabilities"]["qq"]["state"], "ready")
                self.assertEqual(payload["capabilities"]["wechat"]["state"], "missing_config")
                self.assertEqual(payload["summary"]["ready"], 8)
                self.assertIn("frontend_contract", payload)
                serialized = json.dumps(payload).lower()
                self.assertNotIn("api_key", serialized)
                self.assertNotIn("secret_configured", serialized)
                self.assertNotIn("configured-value", serialized)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)
                for handler in list(logger.handlers):
                    logger.removeHandler(handler)
                    handler.close()
                logging.shutdown()

    def test_frontend_contract_exposes_bailongma_adapter_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = make_config(base)
            logger = configure_logging(config.log_dir)
            server = build_server(config, logger)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

            try:
                url = f"http://127.0.0.1:{server.server_port}/frontend/contract"
                with urlopen(url, timeout=2) as response:
                    payload = json.loads(response.read().decode("utf-8"))

                self.assertEqual(payload["status"], "ok")
                self.assertEqual(
                    payload["endpoints"]["social_turn"]["path"],
                    "/social/turn",
                )
                self.assertEqual(
                    payload["endpoints"]["jobs_event"]["path"],
                    "/jobs/event",
                )
                self.assertTrue(
                    payload["frontend_states"]["quick_ack"]["send_ack_first"]
                )
                self.assertEqual(
                    payload["route_ui"]["image_generate"]["progress_kind"],
                    "image_generation",
                )
                self.assertEqual(
                    payload["channel_planes"]["feishu"]["plane"],
                    "company",
                )
                self.assertFalse(
                    payload["channel_planes"]["wechat"]["can_do_company_write"]
                )
                serialized = json.dumps(payload).lower()
                self.assertNotIn("api_key_configured", serialized)
                self.assertNotIn("password-value", serialized)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)
                for handler in list(logger.handlers):
                    logger.removeHandler(handler)
                    handler.close()
                logging.shutdown()

    def test_route_endpoint_classifies_fast_slow_and_risk_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = make_config(base)
            logger = configure_logging(config.log_dir)
            server = build_server(config, logger)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

            try:
                route_url = f"http://127.0.0.1:{server.server_port}/route"

                with urlopen(route_url + "?message=ok", timeout=2) as response:
                    casual = json.loads(response.read().decode("utf-8"))
                self.assertEqual(casual["route"]["route"], "casual_chat")
                self.assertFalse(casual["route"]["quick_ack"])
                self.assertFalse(casual["route"]["async_required"])

                with urlopen(
                    route_url + "?message=generate%20image%20avatar",
                    timeout=2,
                ) as response:
                    image = json.loads(response.read().decode("utf-8"))
                self.assertEqual(image["route"]["route"], "image_generate")
                self.assertEqual(image["route"]["model_slot"], "image_generation")
                self.assertTrue(image["route"]["quick_ack"])
                self.assertTrue(image["route"]["async_required"])

                with urlopen(
                    route_url + "?message=approve%20expense%20payment",
                    timeout=2,
                ) as response:
                    risk = json.loads(response.read().decode("utf-8"))
                self.assertEqual(risk["route"]["route"], "high_risk")
                self.assertTrue(risk["route"]["approval_required"])
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)
                for handler in list(logger.handlers):
                    logger.removeHandler(handler)
                    handler.close()
                logging.shutdown()

    def test_latency_endpoints_record_route_and_external_turns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = make_config(base)
            logger = configure_logging(config.log_dir)
            server = build_server(config, logger)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

            try:
                base_url = f"http://127.0.0.1:{server.server_port}"

                with urlopen(
                    base_url + "/route?message=generate%20image%20avatar",
                    timeout=2,
                ) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                self.assertEqual(payload["route"]["route"], "image_generate")

                external_body = json.dumps(
                    {
                        "turn_id": "test-turn",
                        "route": "image_generate",
                        "status": "completed",
                        "stages": {
                            "intake_ms": 10,
                            "quick_ack_ms": 900,
                            "tool_ms": 42000,
                            "total_ms": 43000,
                            "message": "must be ignored",
                        },
                    }
                ).encode("utf-8")
                request = Request(
                    base_url + "/latency/turn",
                    data=external_body,
                    method="POST",
                    headers={"Content-Type": "application/json"},
                )
                with urlopen(request, timeout=2) as response:
                    created = json.loads(response.read().decode("utf-8"))
                self.assertEqual(created["status"], "ok")
                self.assertEqual(created["record"]["route"], "image_generate")
                self.assertNotIn("message", created["record"]["stages"])

                with urlopen(base_url + "/latency?limit=10", timeout=2) as response:
                    latency = json.loads(response.read().decode("utf-8"))
                self.assertEqual(latency["status"], "ok")
                self.assertIn("quick_ack_ms", latency["allowed_stages"])
                routes = [item["route"] for item in latency["records"]]
                self.assertIn("image_generate", routes)
                self.assertNotIn("api_key", json.dumps(latency).lower())
                self.assertNotIn("secret", json.dumps(latency).lower())
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)
                for handler in list(logger.handlers):
                    logger.removeHandler(handler)
                    handler.close()
                logging.shutdown()

    def test_context_endpoint_exposes_slim_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = make_config(base)
            logger = configure_logging(config.log_dir)
            server = build_server(config, logger)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

            try:
                base_url = f"http://127.0.0.1:{server.server_port}"
                with urlopen(
                    base_url + "/context?message=generate%20image%20avatar",
                    timeout=2,
                ) as response:
                    payload = json.loads(response.read().decode("utf-8"))

                self.assertEqual(payload["status"], "ok")
                self.assertEqual(payload["route"]["route"], "image_generate")
                self.assertEqual(
                    payload["context_budget"]["tool_schema_group"],
                    "image_generation",
                )
                self.assertLessEqual(payload["context_budget"]["max_recent_messages"], 4)
                self.assertFalse(payload["context_budget"]["allow_long_term_memory"])
                self.assertNotIn("api_key", json.dumps(payload).lower())
                self.assertNotIn("secret", json.dumps(payload).lower())
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)
                for handler in list(logger.handlers):
                    logger.removeHandler(handler)
                    handler.close()
                logging.shutdown()

    def test_async_job_endpoints_track_slow_work_without_body_storage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = make_config(base)
            logger = configure_logging(config.log_dir)
            server = build_server(config, logger)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

            try:
                base_url = f"http://127.0.0.1:{server.server_port}"
                user_input = "make a cute sticker with hidden phrase"
                create_body = json.dumps(
                    {
                        "route": "image_generate",
                        "channel": "wechat",
                        "target_id": "room-1",
                        "input": user_input,
                        "tool_name": "image_generation",
                    }
                ).encode("utf-8")
                create_request = Request(
                    base_url + "/jobs",
                    data=create_body,
                    method="POST",
                    headers={"Content-Type": "application/json"},
                )
                with urlopen(create_request, timeout=2) as response:
                    created = json.loads(response.read().decode("utf-8"))

                job = created["job"]
                self.assertEqual(created["status"], "ok")
                self.assertEqual(job["route"], "image_generate")
                self.assertEqual(job["status"], "queued")
                self.assertEqual(job["input_preview_chars"], len(user_input))
                self.assertNotIn("hidden phrase", json.dumps(job))

                transition_body = json.dumps(
                    {"job_id": job["job_id"], "status": "running"}
                ).encode("utf-8")
                transition_request = Request(
                    base_url + "/jobs/transition",
                    data=transition_body,
                    method="POST",
                    headers={"Content-Type": "application/json"},
                )
                with urlopen(transition_request, timeout=2) as response:
                    running = json.loads(response.read().decode("utf-8"))
                self.assertEqual(running["job"]["status"], "running")

                complete_body = json.dumps(
                    {
                        "job_id": job["job_id"],
                        "status": "completed",
                        "result_pointer": "asset://sticker/result-1",
                    }
                ).encode("utf-8")
                complete_request = Request(
                    base_url + "/jobs/transition",
                    data=complete_body,
                    method="POST",
                    headers={"Content-Type": "application/json"},
                )
                with urlopen(complete_request, timeout=2) as response:
                    completed = json.loads(response.read().decode("utf-8"))
                self.assertEqual(completed["job"]["status"], "completed")
                self.assertEqual(
                    completed["job"]["result_pointer"],
                    "asset://sticker/result-1",
                )

                with urlopen(base_url + "/jobs?limit=5", timeout=2) as response:
                    jobs = json.loads(response.read().decode("utf-8"))
                self.assertEqual(jobs["status"], "ok")
                self.assertEqual(jobs["jobs"][0]["job_id"], job["job_id"])
                self.assertNotIn("hidden phrase", json.dumps(jobs))
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)
                for handler in list(logger.handlers):
                    logger.removeHandler(handler)
                    handler.close()
                logging.shutdown()

    def test_social_turn_plans_quick_ack_and_async_job(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = make_config(base)
            logger = configure_logging(config.log_dir)
            server = build_server(config, logger)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

            try:
                base_url = f"http://127.0.0.1:{server.server_port}"
                user_input = "generate image avatar with hidden phrase"
                body = json.dumps(
                    {
                        "channel": "wechat",
                        "target_id": "user-1",
                        "message": user_input,
                    }
                ).encode("utf-8")
                request = Request(
                    base_url + "/social/turn",
                    data=body,
                    method="POST",
                    headers={"Content-Type": "application/json"},
                )
                with urlopen(request, timeout=2) as response:
                    payload = json.loads(response.read().decode("utf-8"))

                self.assertEqual(payload["status"], "ok")
                self.assertEqual(payload["first_action"], "quick_ack")
                self.assertTrue(payload["ack"]["should_send"])
                self.assertIn("\u9a6c\u4e0a", payload["ack"]["text"])
                self.assertEqual(payload["route"]["route"], "image_generate")
                self.assertEqual(payload["context_budget"]["max_recent_messages"], 4)
                self.assertIsNotNone(payload["job"])
                self.assertEqual(payload["job"]["status"], "queued")
                self.assertEqual(payload["job"]["tool_name"], "image_generation")
                self.assertEqual(payload["ack"]["next_job_status_after_send"], "acknowledged")
                self.assertNotIn("hidden phrase", json.dumps(payload))
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)
                for handler in list(logger.handlers):
                    logger.removeHandler(handler)
                    handler.close()
                logging.shutdown()

    def test_job_event_endpoint_advances_worker_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = make_config(base)
            logger = configure_logging(config.log_dir)
            server = build_server(config, logger)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

            try:
                base_url = f"http://127.0.0.1:{server.server_port}"
                create_body = json.dumps(
                    {
                        "route": "image_generate",
                        "channel": "wechat",
                        "target_id": "room-3",
                        "input": "generate image avatar",
                        "tool_name": "image_generation",
                    }
                ).encode("utf-8")
                create_request = Request(
                    base_url + "/jobs",
                    data=create_body,
                    method="POST",
                    headers={"Content-Type": "application/json"},
                )
                with urlopen(create_request, timeout=2) as response:
                    created = json.loads(response.read().decode("utf-8"))
                job_id = created["job"]["job_id"]

                events = [
                    ("ack_sent", "acknowledged"),
                    ("worker_started", "running"),
                    ("worker_completed", "completed"),
                    ("final_delivered", "delivered"),
                ]
                for event, expected_status in events:
                    body = {"job_id": job_id, "event": event}
                    if event == "worker_completed":
                        body["result_pointer"] = "asset://image/result-2"
                    event_request = Request(
                        base_url + "/jobs/event",
                        data=json.dumps(body).encode("utf-8"),
                        method="POST",
                        headers={"Content-Type": "application/json"},
                    )
                    with urlopen(event_request, timeout=2) as response:
                        payload = json.loads(response.read().decode("utf-8"))
                    self.assertEqual(payload["status"], "ok")
                    self.assertEqual(payload["job"]["status"], expected_status)

                with urlopen(base_url + "/jobs?limit=5", timeout=2) as response:
                    jobs = json.loads(response.read().decode("utf-8"))
                self.assertIn("worker_completed", jobs["allowed_events"])
                self.assertEqual(jobs["jobs"][-1]["status"], "delivered")
                self.assertEqual(
                    jobs["jobs"][-1]["result_pointer"],
                    "asset://image/result-2",
                )
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)
                for handler in list(logger.handlers):
                    logger.removeHandler(handler)
                    handler.close()
                logging.shutdown()

    def test_connector_client_wraps_social_turn_and_job_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = make_config(base)
            logger = configure_logging(config.log_dir)
            server = build_server(config, logger)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

            try:
                client = HermesConnectorClient(
                    f"http://127.0.0.1:{server.server_port}",
                    timeout_seconds=2,
                )
                plan = client.plan_social_turn(
                    channel="feishu",
                    target_id="chat-42",
                    message="generate image avatar with hidden phrase",
                )
                self.assertEqual(plan["first_action"], "quick_ack")
                self.assertIsNotNone(plan["job"])
                self.assertNotIn("hidden phrase", json.dumps(plan))

                job_id = plan["job"]["job_id"]
                acknowledged = client.report_job_event(
                    job_id=job_id,
                    event="ack_sent",
                )
                self.assertEqual(acknowledged["job"]["status"], "acknowledged")

                running = client.report_job_event(
                    job_id=job_id,
                    event="worker_started",
                )
                self.assertEqual(running["job"]["status"], "running")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)
                for handler in list(logger.handlers):
                    logger.removeHandler(handler)
                    handler.close()
                logging.shutdown()

    def test_connector_client_supports_server_basic_auth_from_env(self) -> None:
        env = {
            "HERMES_RUNTIME_BASE_URL": "https://example.invalid/runtime",
            "HERMES_RUNTIME_TIMEOUT_SECONDS": "7",
            "HERMES_RUNTIME_BASIC_USER": "runtime-user",
            "HERMES_RUNTIME_BASIC_PASSWORD": "credential-value",
        }

        with patch.dict("os.environ", env, clear=True):
            client = HermesConnectorClient.from_env()

        self.assertEqual(client.base_url, "https://example.invalid/runtime/")
        self.assertEqual(client.timeout_seconds, 7)
        self.assertEqual(
            client._headers()["Authorization"],
            "Basic cnVudGltZS11c2VyOmNyZWRlbnRpYWwtdmFsdWU=",
        )

    def test_social_turn_appends_follow_up_to_active_job(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = make_config(base)
            logger = configure_logging(config.log_dir)
            server = build_server(config, logger)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

            try:
                base_url = f"http://127.0.0.1:{server.server_port}"
                first_body = json.dumps(
                    {
                        "channel": "wechat",
                        "target_id": "room-2",
                        "message": "generate image avatar",
                    }
                ).encode("utf-8")
                first_request = Request(
                    base_url + "/social/turn",
                    data=first_body,
                    method="POST",
                    headers={"Content-Type": "application/json"},
                )
                with urlopen(first_request, timeout=2) as response:
                    first = json.loads(response.read().decode("utf-8"))
                self.assertEqual(first["first_action"], "quick_ack")
                self.assertIsNotNone(first["job"])

                follow_up_body = json.dumps(
                    {
                        "channel": "wechat",
                        "target_id": "room-2",
                        "message": "make it softer with hidden phrase",
                    }
                ).encode("utf-8")
                follow_up_request = Request(
                    base_url + "/social/turn",
                    data=follow_up_body,
                    method="POST",
                    headers={"Content-Type": "application/json"},
                )
                with urlopen(follow_up_request, timeout=2) as response:
                    follow_up = json.loads(response.read().decode("utf-8"))

                self.assertEqual(follow_up["status"], "ok")
                self.assertEqual(follow_up["first_action"], "append_to_active_job")
                self.assertTrue(follow_up["ack"]["should_send"])
                self.assertIn("\u6ca1\u4e22", follow_up["ack"]["text"])
                self.assertIsNone(follow_up["job"])
                self.assertEqual(
                    follow_up["active_job"]["job_id"],
                    first["job"]["job_id"],
                )
                self.assertEqual(
                    follow_up["context_budget"]["memory_depth"],
                    "follow_up_delta",
                )
                self.assertNotIn("hidden phrase", json.dumps(follow_up))
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)
                for handler in list(logger.handlers):
                    logger.removeHandler(handler)
                    handler.close()
                logging.shutdown()

    def test_social_turn_keeps_tiny_chat_on_direct_reply_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = make_config(base)
            logger = configure_logging(config.log_dir)
            server = build_server(config, logger)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

            try:
                base_url = f"http://127.0.0.1:{server.server_port}"
                body = json.dumps(
                    {
                        "channel": "feishu",
                        "target_id": "chat-1",
                        "message": "ok",
                    }
                ).encode("utf-8")
                request = Request(
                    base_url + "/social/turn",
                    data=body,
                    method="POST",
                    headers={"Content-Type": "application/json"},
                )
                with urlopen(request, timeout=2) as response:
                    payload = json.loads(response.read().decode("utf-8"))

                self.assertEqual(payload["status"], "ok")
                self.assertEqual(payload["first_action"], "direct_reply")
                self.assertFalse(payload["ack"]["should_send"])
                self.assertEqual(payload["ack"]["text"], "")
                self.assertEqual(payload["route"]["route"], "casual_chat")
                self.assertIsNone(payload["job"])
                self.assertEqual(payload["context_budget"]["tool_schema_group"], "send_only")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)
                for handler in list(logger.handlers):
                    logger.removeHandler(handler)
                    handler.close()
                logging.shutdown()


if __name__ == "__main__":
    unittest.main()


