from __future__ import annotations

import argparse
import getpass
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .auth import PasswordHashError, is_password_hash_valid, verify_password
from .config import get_data_dir
from .errors import BookRentalError
from .service import BookRentalService, iso
from .store import BOOK_FORMAT_PDF, CsvStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="BookBridge 관리자 및 인증 진단 도구")
    subparsers = parser.add_subparsers(dest="command")
    create = subparsers.add_parser("create-admin", help="관리자 계정을 생성합니다.")
    create.add_argument("--military-id", default=os.environ.get("BOOKBRIDGE_ADMIN_ID"))
    create.add_argument("--password", default=os.environ.get("BOOKBRIDGE_ADMIN_PASSWORD"))
    create.add_argument("--name", default=os.environ.get("BOOKBRIDGE_ADMIN_NAME", "관리자"))
    create.add_argument("--data-dir", help="BOOKBRIDGE_DATA_DIR보다 우선하는 데이터 디렉터리")
    debug = subparsers.add_parser("debug-login", help="사용자 CSV와 비밀번호 검증 상태를 안전하게 진단합니다.")
    debug.add_argument("--military-id", required=True)
    debug.add_argument("--data-dir", help="BOOKBRIDGE_DATA_DIR보다 우선하는 데이터 디렉터리")
    migrate = subparsers.add_parser("migrate-pdf-loans", help="기존 활성 PDF 대출을 반납 완료로 종료합니다.")
    migrate.add_argument("--data-dir", help="BOOKBRIDGE_DATA_DIR보다 우선하는 데이터 디렉터리")
    mode = migrate.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="변경 없이 대상 건수만 확인합니다.")
    mode.add_argument("--apply", action="store_true", help="백업 후 활성 PDF 대출을 RETURNED로 변경합니다.")
    return parser


def resolve_data_dir(command_line_value: str | None = None) -> Path:
    if command_line_value:
        return Path(command_line_value).expanduser().resolve()
    return get_data_dir()


def debug_login(data_dir: Path, military_id: str) -> int:
    store = CsvStore(data_dir)
    users_path = store.path("users")
    normalized_id = str(military_id).strip()
    print(f"사용 데이터 디렉터리: {data_dir}")
    print(f"users.csv 경로: {users_path}")
    users = store.read_users()
    user = next((row for row in users if row["military_id"].casefold() == normalized_id.casefold()), None)
    print(f"사용자 존재 여부: {'예' if user else '아니요'}")
    if user is None:
        return 1
    print(f"active 상태: {store.is_active(user['active'])}")
    print(f"role: {user['role']}")
    valid_format = is_password_hash_valid(user["password_hash"])
    print(f"password_hash 포맷 정상 여부: {valid_format}")
    if not valid_format:
        return 1
    password = getpass.getpass("비밀번호: ")
    try:
        verified = verify_password(password, user["password_hash"])
    except PasswordHashError as error:
        print(f"비밀번호 해시 검증 오류: {error}")
        return 1
    print(f"비밀번호 검증: {'성공' if verified else '실패'}")
    return 0 if verified and store.is_active(user["active"]) else 1


def migrate_pdf_loans(data_dir: Path, *, apply: bool = False) -> int:
    store = CsvStore(data_dir)
    books = store.read("books")
    book_by_id = {row["id"]: row for row in books}
    pdf_book_ids = {row["id"] for row in books if row["format"] == BOOK_FORMAT_PDF}
    requests = store.read("borrow_requests")
    loans = store.read("loans")
    pdf_requests = [row for row in requests if row.get("book_id") in pdf_book_ids]
    active_pdf_loans = [row for row in loans if row.get("book_id") in pdf_book_ids and row.get("status") in {"LOANED", "OVERDUE"}]
    anomalies = []
    for row in requests:
        if row.get("book_id") not in book_by_id:
            anomalies.append(f"borrow_requests.csv #{row.get('id', '?')} missing book_id={row.get('book_id', '')}")
    for row in loans:
        if row.get("book_id") not in book_by_id:
            anomalies.append(f"loans.csv #{row.get('id', '?')} missing book_id={row.get('book_id', '')}")

    print(f"대상 PDF 책 수: {len(pdf_book_ids)}")
    print(f"기존 PDF 요청 수: {len(pdf_requests)}")
    print(f"활성 PDF 대출 수: {len(active_pdf_loans)}")
    print(f"변경될 행 수: {len(active_pdf_loans)}")
    print(f"데이터 이상 항목: {len(anomalies)}")
    for item in anomalies:
        print(f"- {item}")

    if not apply:
        return 0
    if not active_pdf_loans:
        print("변경할 활성 PDF 대출이 없습니다.")
        return 0

    backup_dir = _backup_tables(store, ["loans", "admin_logs"])
    now = datetime.now(timezone.utc)
    active_ids = {row["id"] for row in active_pdf_loans}
    with store.transaction():
        loans = store.read("loans")
        changed = []
        for loan in loans:
            if loan["id"] in active_ids and loan["status"] in {"LOANED", "OVERDUE"}:
                before = dict(loan)
                loan.update(status="RETURNED", returned_at=iso(now), updated_at=iso(now))
                changed.append((before, dict(loan)))
        store.write("loans", loans)
        logs = store.read("admin_logs")
        for before, after in changed:
            logs.append({
                "id": str(store.next_id(logs)),
                "admin_id": "0",
                "admin_name": "CLI",
                "action": "PDF_LOAN_MIGRATED",
                "target_type": "CSV_ROW",
                "target_file": "loans.csv",
                "target_id": after["id"],
                "memo": "기존 활성 PDF 대출을 디지털 자료 정책에 맞게 RETURNED로 종료",
                "before_summary": json.dumps(before, ensure_ascii=False, sort_keys=True)[:2000],
                "after_summary": json.dumps(after, ensure_ascii=False, sort_keys=True)[:2000],
                "created_at": iso(now),
            })
        store.write("admin_logs", logs)
    print(f"백업 디렉터리: {backup_dir}")
    print(f"마이그레이션 완료: {len(active_ids)}건")
    return 0


def _backup_tables(store: CsvStore, tables: list[str]) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    backup_dir = store.data_dir / "backups" / f"pdf_loan_migration_{stamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    for table in tables:
        shutil.copy2(store.path(table), backup_dir / f"{table}.csv")
    return backup_dir


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "debug-login":
        try:
            return debug_login(resolve_data_dir(args.data_dir), args.military_id)
        except Exception as error:
            print(f"로그인 진단 중 오류가 발생했습니다: {type(error).__name__}: {error}")
            return 1
    if args.command == "migrate-pdf-loans":
        try:
            return migrate_pdf_loans(resolve_data_dir(args.data_dir), apply=args.apply)
        except Exception as error:
            print(f"PDF 대출 마이그레이션 중 오류가 발생했습니다: {type(error).__name__}: {error}")
            return 1
    if args.command != "create-admin":
        parser.print_help()
        return 2
    if not args.military_id or not args.password or not args.name:
        parser.error("군번, 비밀번호, 이름을 인자 또는 환경변수로 입력해 주세요.")
    try:
        data_dir = resolve_data_dir(args.data_dir)
        print(f"사용 데이터 디렉터리: {data_dir}")
        service = BookRentalService(CsvStore(data_dir))
        user, created = service.create_admin(args.name, args.military_id, args.password)
    except BookRentalError as error:
        print(f"관리자 생성 실패: {error}")
        return 1
    if created:
        print(f"관리자 계정을 생성했습니다: {user['name']} ({user['military_id']})")
    else:
        print(f"이미 같은 군번의 관리자 계정이 있습니다: {user['military_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
