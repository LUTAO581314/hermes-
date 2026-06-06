"""Configuration loading for the minimal Hermes runtime."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: str | None, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class RuntimeConfig:
    app_name: str
    env: str
    host: str
    port: int
    log_dir: Path
    data_dir: Path
    obsidian_vault_dir: Path
    safe_mode: bool
    enable_feishu_smoke: bool


def load_config() -> RuntimeConfig:
    data_dir = Path(os.getenv("HERMES_DATA_DIR", "./data")).resolve()
    log_dir = Path(os.getenv("HERMES_LOG_DIR", "./logs")).resolve()
    obsidian_vault_dir = Path(
        os.getenv("HERMES_OBSIDIAN_VAULT_DIR", "./obsidian-vault")
    ).resolve()

    return RuntimeConfig(
        app_name=os.getenv("HERMES_APP_NAME", "hermes-runtime"),
        env=os.getenv("HERMES_ENV", "development"),
        host=os.getenv("HERMES_HOST", "127.0.0.1"),
        port=_as_int(os.getenv("HERMES_PORT"), 8787),
        log_dir=log_dir,
        data_dir=data_dir,
        obsidian_vault_dir=obsidian_vault_dir,
        safe_mode=_as_bool(os.getenv("HERMES_SAFE_MODE"), True),
        enable_feishu_smoke=_as_bool(os.getenv("HERMES_ENABLE_FEISHU_SMOKE"), False),
    )
