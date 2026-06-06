from __future__ import annotations

import json
import logging
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.request import urlopen

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
                "HERMES_WECHAT_MODE": "planned",
                "HERMES_WECHAT_CHANNEL": "wecom_customer_service",
                "HERMES_WECHAT_PERSONA_MODE": "companion",
                "HERMES_WECHAT_PROACTIVE_CHAT": "true",
                "HERMES_WECHAT_MAX_DAILY_PROACTIVE_MESSAGES": "2",
                "HERMES_WECHAT_PERSONAL_BRIDGE_ENABLED": "false",
                "HERMES_WECHAT_OFFICIAL_APP_SECRET": "test-secret",
                "HERMES_WECOM_SECRET": "test-secret",
            }

            with patch.dict("os.environ", env, clear=True):
                config = load_config()

            self.assertEqual(config.wechat_mode, "planned")
            self.assertEqual(config.wechat_channel, "wecom_customer_service")
            self.assertEqual(config.wechat_persona_mode, "companion")
            self.assertTrue(config.wechat_proactive_chat)
            self.assertEqual(config.wechat_max_daily_proactive_messages, 2)
            self.assertFalse(config.wechat_personal_bridge_enabled)
            self.assertTrue(config.wechat_official_app_secret_configured)
            self.assertTrue(config.wecom_secret_configured)

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
