from __future__ import annotations

import json
import logging
from pathlib import Path
import tempfile
import threading
import time
import unittest
from urllib.request import urlopen

from hermes_runtime.config import RuntimeConfig
from hermes_runtime.logging_utils import configure_logging
from hermes_runtime.server import build_server, readiness


class RuntimeTests(unittest.TestCase):
    def test_readiness_is_ready_after_directories_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = RuntimeConfig(
                app_name="test-hermes",
                env="test",
                host="127.0.0.1",
                port=0,
                log_dir=base / "logs",
                data_dir=base / "data",
                obsidian_vault_dir=base / "obsidian-vault",
                safe_mode=True,
                enable_feishu_smoke=False,
                search_mode="external_project",
                search_project="trendradar",
                trendradar_base_url="",
                trendradar_mcp_command="",
                searxng_base_url="",
                ai_provider="supermoxi",
                ai_base_url="https://api.supermoxi.cn",
                ai_api_key_configured=False,
                ai_default_model="",
                ai_fast_model="",
                ai_reasoning_model="",
                ai_vision_model="",
                ai_timeout_seconds=60,
            )
            config.log_dir.mkdir()
            config.data_dir.mkdir()
            config.obsidian_vault_dir.mkdir()

            result = readiness(config)

            self.assertEqual(result["status"], "ready")
            self.assertTrue(all(result["checks"].values()))

    def test_health_endpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = RuntimeConfig(
                app_name="test-hermes",
                env="test",
                host="127.0.0.1",
                port=0,
                log_dir=base / "logs",
                data_dir=base / "data",
                obsidian_vault_dir=base / "obsidian-vault",
                safe_mode=True,
                enable_feishu_smoke=False,
                search_mode="external_project",
                search_project="trendradar",
                trendradar_base_url="",
                trendradar_mcp_command="",
                searxng_base_url="",
                ai_provider="supermoxi",
                ai_base_url="https://api.supermoxi.cn",
                ai_api_key_configured=True,
                ai_default_model="",
                ai_fast_model="",
                ai_reasoning_model="",
                ai_vision_model="",
                ai_timeout_seconds=60,
            )
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
