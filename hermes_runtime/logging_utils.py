"""Structured logging helpers for Hermes runtime."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any


class JsonLineFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "created_at": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def configure_logging(log_dir: Path) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("hermes_runtime")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(JsonLineFormatter())
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(log_dir / "hermes-runtime.jsonl", encoding="utf-8")
    file_handler.setFormatter(JsonLineFormatter())
    logger.addHandler(file_handler)

    return logger
