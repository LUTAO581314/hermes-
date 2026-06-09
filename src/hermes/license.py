from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LicenseState:
    status: str
    path: str
    license_id: str = ""
    organization_id: str = ""
    plan: str = ""
    expires_at: str = ""
    error: str = ""


def load_license(path: Path) -> LicenseState:
    if not path.exists():
        return LicenseState(status="missing_config", path=str(path))
    try:
        payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return LicenseState(status="invalid", path=str(path), error=str(exc))

    return LicenseState(
        status="partial",
        path=str(path),
        license_id=str(payload.get("license_id", "")),
        organization_id=str(payload.get("organization_id", "")),
        plan=str(payload.get("plan", payload.get("plan_code", ""))),
        expires_at=str(payload.get("expires_at", "")),
    )
