from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path

from .auth import PasswordHashError, is_password_hash_valid, verify_password
from .config import get_data_dir
from .errors import BookRentalError
from .service import BookRentalService
from .store import CsvStore


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


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "debug-login":
        try:
            return debug_login(resolve_data_dir(args.data_dir), args.military_id)
        except Exception as error:
            print(f"로그인 진단 중 오류가 발생했습니다: {type(error).__name__}: {error}")
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
