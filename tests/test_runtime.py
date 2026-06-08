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
                "HERMES_WECHAT_OFFICIAL_APP_SECRET": "test-secret",
                "HERMES_WECOM_SECRET": "test-secret",
                "HERMES_STICKER_BRIDGE_ENABLED": "true",
                "HERMES_STICKER_DEFAULT_PROVIDER": "stipop",
                "HERMES_STICKER_DEFAULT_STYLE": "kawaii_anime",
                "HERMES_STICKER_API_KEY": "test-secret",
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
                self.assertIn("马上", payload["ack"]["text"])
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
