from __future__ import annotations

import csv
import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import fcntl

SCHEMAS: dict[str, list[str]] = {
    "users": [
        "id", "name", "military_id", "password_hash", "role", "active",
        "created_at", "updated_at",
    ],
    "books": [
        "id", "lender_id", "title", "author", "category", "description", "format",
        "total_quantity", "available_quantity", "default_loan_days", "status",
        "rejection_memo", "file_name", "file_path", "created_at", "updated_at",
    ],
    "borrow_requests": [
        "id", "borrower_id", "book_id", "quantity", "status", "requested_at",
        "approved_at", "rejected_at", "canceled_at", "rejection_memo", "updated_at",
    ],
    "loans": [
        "id", "borrow_request_id", "borrower_id", "lender_id", "book_id", "quantity",
        "loaned_at", "due_at", "returned_at", "status", "updated_at",
    ],
    "admin_logs": ["id", "admin_id", "action", "target_type", "target_id", "memo", "created_at"],
}


class CsvStore:
    """Small CSV data store with schema migration, locking, and atomic replacement."""

    def __init__(self, data_dir: str | Path = "data") -> None:
        self.data_dir = Path(data_dir)
        self.upload_dir = self.data_dir / "uploads"
        self.lock_path = self.data_dir / ".bookbridge.lock"
        self.initialize()

    def initialize(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.lock_path.touch(exist_ok=True)
        for table, fields in SCHEMAS.items():
            path = self.path(table)
            if not path.exists():
                self._write_file(path, fields, [])
            else:
                self._migrate_file(table, path, fields)

    def _migrate_file(self, table: str, path: Path, fields: list[str]) -> None:
        with path.open(encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            old_fields = reader.fieldnames or []
            rows = list(reader)
        if old_fields == fields:
            return
        if table == "users":
            for row in rows:
                legacy_roles = set(filter(None, row.get("roles", "").split("|")))
                if not row.get("role"):
                    row["role"] = "ADMIN" if "ADMIN" in legacy_roles else "USER"
                row.setdefault("military_id", "")
                row.setdefault("password_hash", "")
                row.setdefault("active", "true")
        self._write_file(path, fields, rows)

    def path(self, table: str) -> Path:
        if table not in SCHEMAS:
            raise KeyError(f"Unknown table: {table}")
        return self.data_dir / f"{table}.csv"

    def read(self, table: str) -> list[dict[str, str]]:
        with self.path(table).open(encoding="utf-8", newline="") as file:
            return list(csv.DictReader(file))

    def write(self, table: str, rows: list[dict[str, object]]) -> None:
        self._write_file(self.path(table), SCHEMAS[table], rows)

    def next_id(self, rows: list[dict[str, str]]) -> int:
        return max((int(row["id"]) for row in rows), default=0) + 1

    @contextmanager
    def transaction(self) -> Iterator["CsvStore"]:
        """Serialize mutations and restore every CSV if a mutation fails."""
        with self.lock_path.open("r+") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            backup_dir = Path(tempfile.mkdtemp(prefix="bookbridge-backup-"))
            try:
                for table in SCHEMAS:
                    shutil.copy2(self.path(table), backup_dir / f"{table}.csv")
                yield self
            except Exception:
                for table in SCHEMAS:
                    os.replace(backup_dir / f"{table}.csv", self.path(table))
                raise
            finally:
                shutil.rmtree(backup_dir, ignore_errors=True)
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def _write_file(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
                writer.writeheader()
                for row in rows:
                    writer.writerow({field: row.get(field, "") for field in fields})
                file.flush()
                os.fsync(file.fileno())
            os.replace(temp_name, path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
