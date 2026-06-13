from __future__ import annotations

from book_rental.admin_command_runner import debug_login
from book_rental.service import BookRentalService
from book_rental.store import CsvStore


def test_debug_login_reports_safe_diagnostics(tmp_path, monkeypatch, capsys):
    data_dir = tmp_path / "data"
    service = BookRentalService(CsvStore(data_dir))
    service.register_user("엄준식", "333", "password333", "password333")
    monkeypatch.setattr("getpass.getpass", lambda prompt: "password333")

    exit_code = debug_login(data_dir.resolve(), "333")
    output = capsys.readouterr().out

    assert exit_code == 0
    assert f"사용 데이터 디렉터리: {data_dir.resolve()}" in output
    assert f"users.csv 경로: {data_dir.resolve() / 'users.csv'}" in output
    assert "사용자 존재 여부: 예" in output
    assert "active 상태: True" in output
    assert "role: USER" in output
    assert "password_hash 포맷 정상 여부: True" in output
    assert "비밀번호 검증: 성공" in output
    assert "pbkdf2_sha256$" not in output
    assert "password333" not in output
