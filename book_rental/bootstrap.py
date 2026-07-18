from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Mapping

from .config import get_app_profile, normalize_profile
from .errors import ValidationError
from .service import BookRentalService

DEV_PROFILE = "dev"
DEV_BOOTSTRAP_FLAG = "DEV_BOOTSTRAP_ADMIN"
DEV_ADMIN_MILITARY_ID = "DEV_ADMIN_MILITARY_ID"
DEV_ADMIN_PASSWORD = "DEV_ADMIN_PASSWORD"
DEV_ADMIN_NAME = "DEV_ADMIN_NAME"
REQUIRED_DEV_ADMIN_ENV = (DEV_ADMIN_MILITARY_ID, DEV_ADMIN_PASSWORD, DEV_ADMIN_NAME)


@dataclass(frozen=True)
class BootstrapResult:
    status: str
    profile: str
    enabled: bool
    message: str = ""
    missing: tuple[str, ...] = ()

    @property
    def created(self) -> bool:
        return self.status == "created"


def bootstrap_dev_admin(
    service: BookRentalService,
    *,
    environ: Mapping[str, str] | None = None,
    logger: logging.Logger | None = None,
) -> BootstrapResult:
    """Create the configured development ADMIN account when explicitly enabled."""
    env = os.environ if environ is None else environ
    log = logger or logging.getLogger("bookbridge.bootstrap")
    profile = get_app_profile() if environ is None else normalize_profile(env.get("APP_PROFILE"))
    enabled = (env.get(DEV_BOOTSTRAP_FLAG) or "").strip().casefold() == "true"

    if profile != DEV_PROFILE:
        log.debug(
            "Development admin bootstrap skipped: profile=%r enabled=%s",
            profile or "[unset]",
            enabled,
        )
        return BootstrapResult("disabled", profile, enabled)

    if not enabled:
        log.debug("Development admin bootstrap skipped: profile=dev enabled=false")
        return BootstrapResult("disabled", profile, enabled)

    missing = tuple(name for name in REQUIRED_DEV_ADMIN_ENV if not (env.get(name) or "").strip())
    if missing:
        log.warning("Development admin bootstrap skipped: missing settings=%s", ", ".join(missing))
        return BootstrapResult(
            "missing_config",
            profile,
            enabled,
            message="개발 관리자 자동 생성 설정이 누락되었습니다.",
            missing=missing,
        )

    name = (env.get(DEV_ADMIN_NAME) or "").strip()
    military_id = (env.get(DEV_ADMIN_MILITARY_ID) or "").strip()
    password = env.get(DEV_ADMIN_PASSWORD) or ""

    try:
        user, created = service.create_admin(name, military_id, password)
    except ValidationError as error:
        users = service.store.read_users()
        existing = next(
            (row for row in users if row["military_id"].casefold() == military_id.casefold()),
            None,
        )
        if existing and existing["role"] != "ADMIN":
            log.error("Development admin bootstrap blocked: military_id conflicts with non-admin user")
            return BootstrapResult(
                "conflict_user",
                profile,
                enabled,
                message="개발 관리자 군번이 기존 일반 사용자와 충돌합니다.",
            )
        log.warning("Development admin bootstrap skipped: invalid configuration: %s", error)
        return BootstrapResult("invalid_config", profile, enabled, message=str(error))

    if created:
        log.info("Development admin account created: military_id=%s", user["military_id"])
        return BootstrapResult("created", profile, enabled)

    log.info("Development admin account already exists: military_id=%s", user["military_id"])
    return BootstrapResult("exists", profile, enabled)
