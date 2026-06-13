from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Callable

from .store import CsvStore

SESSION_MINUTES = 15


class SessionService:
    """Persistent, sliding 15-minute login sessions; only token hashes are stored."""

    def __init__(self, store: CsvStore, clock: Callable[[], datetime] | None = None) -> None:
        self.store = store
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def create(self, user: dict[str, object]) -> str:
        token = secrets.token_urlsafe(48)
        now = self._utc(self.clock())
        self.store.ensure_table("sessions")
        with self.store.transaction():
            sessions = self.store.read("sessions")
            sessions.append({
                "token_hash": self._hash(token), "user_id": str(user["id"]),
                "military_id": str(user["military_id"]), "role": str(user.get("role") or "USER"),
                "created_at": self._iso(now), "expires_at": self._iso(now + timedelta(minutes=SESSION_MINUTES)),
                "revoked_at": "", "last_seen_at": self._iso(now),
            })
            self.store.write("sessions", sessions)
        return token

    def restore(self, token: str) -> dict[str, object] | None:
        if not token:
            return None
        now = self._utc(self.clock())
        with self.store.transaction():
            sessions = self.store.read("sessions")
            session = next((row for row in sessions if secrets.compare_digest(row.get("token_hash", ""), self._hash(token))), None)
            if session is None or session.get("revoked_at"):
                return None
            try:
                expires_at = self._utc(datetime.fromisoformat(session["expires_at"]))
            except (KeyError, TypeError, ValueError):
                return None
            if expires_at <= now:
                return None
            users = self.store.read_users()
            user = next((row for row in users if row["id"] == session.get("user_id")), None)
            if user is None or not self.store.is_active(user["active"]) or user["role"] != session.get("role"):
                return None
            session["last_seen_at"] = self._iso(now)
            session["expires_at"] = self._iso(now + timedelta(minutes=SESSION_MINUTES))
            self.store.write("sessions", sessions)
            return {
                "id": user["id"], "name": user["name"], "military_id": user["military_id"],
                "role": user["role"], "active": True, "created_at": user["created_at"],
                "updated_at": user["updated_at"],
            }

    def revoke(self, token: str) -> None:
        if not token:
            return
        with self.store.transaction():
            sessions = self.store.read("sessions")
            for session in sessions:
                if secrets.compare_digest(session.get("token_hash", ""), self._hash(token)) and not session.get("revoked_at"):
                    session["revoked_at"] = self._iso(self.clock())
            self.store.write("sessions", sessions)

    @staticmethod
    def _hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @classmethod
    def _iso(cls, value: datetime) -> str:
        return cls._utc(value).isoformat(timespec="seconds")

    @staticmethod
    def _utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
