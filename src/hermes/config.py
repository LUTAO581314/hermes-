from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    product_name: str
    brand_key: str
    trademark_name: str
    logo_text: str
    env: str
    host: str
    port: int
    database_url: str
    data_dir: Path
    log_dir: Path
    obsidian_vault_dir: Path
    license_file: Path
    platform_base_url: str
    server_id: str
    vendor_dir: Path

    @property
    def has_database(self) -> bool:
        return bool(self.database_url.strip())


def load_settings() -> Settings:
    root = Path(__file__).resolve().parents[2]
    return Settings(
        product_name=os.getenv("BAIRUI_PRODUCT_NAME", os.getenv("MOXI_PRODUCT_NAME", "bairui Agent OS")),
        brand_key=os.getenv("BAIRUI_BRAND_KEY", "bairui"),
        trademark_name=os.getenv("BAIRUI_TRADEMARK_NAME", "bairui"),
        logo_text=os.getenv("BAIRUI_LOGO_TEXT", "bairui"),
        env=os.getenv("HERMES_ENV", "development"),
        host=os.getenv("HERMES_HOST", "127.0.0.1"),
        port=int(os.getenv("HERMES_PORT", "8787")),
        database_url=os.getenv("HERMES_DATABASE_URL", ""),
        data_dir=Path(os.getenv("HERMES_DATA_DIR", "./data/hermes")),
        log_dir=Path(os.getenv("HERMES_LOG_DIR", "./logs/hermes")),
        obsidian_vault_dir=Path(os.getenv("HERMES_OBSIDIAN_VAULT_DIR", "./obsidian-vault")),
        license_file=Path(os.getenv("MOXI_LICENSE_FILE", "./license/moxi-license.json")),
        platform_base_url=os.getenv("MOXI_PLATFORM_BASE_URL", ""),
        server_id=os.getenv("MOXI_SERVER_ID", ""),
        vendor_dir=root / "vendor" / "runtimes",
    )


def ensure_runtime_dirs(settings: Settings) -> None:
    for path in (settings.data_dir, settings.log_dir, settings.obsidian_vault_dir):
        path.mkdir(parents=True, exist_ok=True)
