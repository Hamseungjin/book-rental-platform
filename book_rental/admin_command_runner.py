from __future__ import annotations

import argparse
import os
from pathlib import Path

from .config import get_data_dir
from .errors import BookRentalError
from .service import BookRentalService
from .store import CsvStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="BookBridge 관리자 계정 관리")
    subparsers = parser.add_subparsers(dest="command")
    create = subparsers.add_parser("create-admin", help="관리자 계정을 생성합니다.")
    create.add_argument("--military-id", default=os.environ.get("BOOKBRIDGE_ADMIN_ID"))
    create.add_argument("--password", default=os.environ.get("BOOKBRIDGE_ADMIN_PASSWORD"))
    create.add_argument("--name", default=os.environ.get("BOOKBRIDGE_ADMIN_NAME", "관리자"))
    create.add_argument("--data-dir", help="BOOKBRIDGE_DATA_DIR보다 우선하는 데이터 디렉터리")
    return parser


def resolve_data_dir(command_line_value: str | None = None) -> Path:
    if command_line_value:
        return Path(command_line_value).expanduser().resolve()
    return get_data_dir()


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
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
