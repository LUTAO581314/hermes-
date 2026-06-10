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
    license_secret: str
    platform_base_url: str
    server_id: str
    vendor_dir: Path
    model_base_url: str
    model_api_key: str
    model_name: str
    model_timeout_seconds: int
    everos_base_url: str
    everos_memory_root: Path
    everos_timeout_seconds: int
    trendradar_project_root: Path | None
    trendradar_mcp_url: str
    trendradar_timeout_seconds: int
    mirofish_project_root: Path | None
    mirofish_backend_base_url: str
    mirofish_frontend_base_url: str
    mirofish_timeout_seconds: int

    @property
    def has_database(self) -> bool:
        return bool(self.database_url.strip())

    @property
    def has_model_gateway(self) -> bool:
        return bool(self.model_base_url.strip() and self.model_api_key.strip() and self.model_name.strip())


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
        license_secret=os.getenv("BAIRUI_LICENSE_SECRET", ""),
        platform_base_url=os.getenv("MOXI_PLATFORM_BASE_URL", ""),
        server_id=os.getenv("MOXI_SERVER_ID", ""),
        vendor_dir=root / "vendor" / "runtimes",
        model_base_url=os.getenv("BAIRUI_MODEL_BASE_URL", ""),
        model_api_key=os.getenv("BAIRUI_MODEL_API_KEY", ""),
        model_name=os.getenv("BAIRUI_MODEL_NAME", ""),
        model_timeout_seconds=int(os.getenv("BAIRUI_MODEL_TIMEOUT_SECONDS", "60")),
        everos_base_url=os.getenv("EVEROS_BASE_URL", ""),
        everos_memory_root=Path(os.getenv("EVEROS_MEMORY_ROOT", "./data/everos")),
        everos_timeout_seconds=int(os.getenv("EVEROS_TIMEOUT_SECONDS", "30")),
        trendradar_project_root=Path(os.environ["TRENDRADAR_PROJECT_ROOT"]) if os.getenv("TRENDRADAR_PROJECT_ROOT") else None,
        trendradar_mcp_url=os.getenv("TRENDRADAR_MCP_URL", ""),
        trendradar_timeout_seconds=int(os.getenv("TRENDRADAR_TIMEOUT_SECONDS", "30")),
        mirofish_project_root=Path(os.environ["MIROFISH_PROJECT_ROOT"]) if os.getenv("MIROFISH_PROJECT_ROOT") else None,
        mirofish_backend_base_url=os.getenv("MIROFISH_BACKEND_BASE_URL", ""),
        mirofish_frontend_base_url=os.getenv("MIROFISH_FRONTEND_BASE_URL", ""),
        mirofish_timeout_seconds=int(os.getenv("MIROFISH_TIMEOUT_SECONDS", "30")),
    )


def ensure_runtime_dirs(settings: Settings) -> None:
    for path in (settings.data_dir, settings.log_dir, settings.obsidian_vault_dir, settings.everos_memory_root):
        path.mkdir(parents=True, exist_ok=True)
