# BookBridge

Streamlit과 CSV 저장소로 만든 책 대여 플랫폼입니다. 군번 기반 회원가입/로그인을 제공하며, 일반 회원은 도서 등록과 대여를 모두 이용하고 관리자는 승인, 현황, 사용자, CSV 데이터를 관리합니다.

## 주요 기능

- 군번을 로그인 ID로 사용하는 회원가입, 로그인, 로그아웃
- PBKDF2-SHA256 비밀번호 해시 저장, 평문 비밀번호 미저장
- 비로그인 사용자의 승인 도서 조회
- 일반 회원의 실물 도서 등록, 대여 요청, 반납 처리
- 일반 회원의 PDF 자료 등록 및 승인 후 다운로드
- 관리자의 도서 승인/거절, 대여 승인/거절, 전체 대출 조회, 사용자 관리
- 관리자 데이터 관리 화면에서 CSV 조회/편집, 백업, 변경 로그 기록
- 15분 sliding expiration 방식의 쿠키 기반 로그인 유지
- CSV 스키마 자동 생성/마이그레이션, 잠금과 원자적 저장

## 실행

Python 3.11 이상을 권장합니다.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Windows PowerShell에서는 가상환경 활성화만 다음처럼 실행합니다.

```powershell
.\.venv\Scripts\Activate.ps1
```

앱은 기본적으로 `http://localhost:8501`에서 열립니다.

## 관리자 계정

관리자는 회원가입 화면에서 만들 수 없습니다. 최초 관리자 계정은 CLI로 생성합니다.

```bash
python -m book_rental.admin_command_runner create-admin \
  --military-id admin \
  --password '안전한-비밀번호' \
  --name 관리자
```

환경변수로도 전달할 수 있습니다.

```bash
export BOOKBRIDGE_ADMIN_ID=admin
export BOOKBRIDGE_ADMIN_PASSWORD='안전한-비밀번호'
export BOOKBRIDGE_ADMIN_NAME=관리자
python -m book_rental.admin_command_runner create-admin
```

개발 환경에서만 자동 관리자 생성을 켤 수 있습니다.

```bash
python.exe -m book_rental.admin_command_runner create-admin \
  --military-id admin \
  --password 'admin1234!' \
  --name '개발 관리자' \
  --data-dir './data'
```

`APP_PROFILE=prod`이거나 `DEV_BOOTSTRAP_ADMIN=true`가 아니면 자동 생성은 동작하지 않습니다.

## 데이터

기본 데이터 디렉터리는 프로젝트 루트의 `data/`입니다. 앱, `CsvStore`, 관리자 CLI는 모두 같은 경로 결정 로직을 사용합니다.

```bash
export BOOKBRIDGE_DATA_DIR=/opt/bookbridge/data
streamlit run app.py
```

사용 CSV는 다음과 같습니다.

- `users.csv`: 사용자, 군번, 비밀번호 해시, 역할, 활성 상태
- `books.csv`: 실물 도서와 PDF 자료 정보, 승인 상태, 업로드 경로
- `borrow_requests.csv`: 실물 도서 대여 요청
- `loans.csv`: 승인된 실물 도서 대출과 반납 상태
- `admin_logs.csv`: 관리자 승인/CSV 편집/비밀번호 재설정 로그
- `sessions.csv`: 로그인 유지 토큰 해시와 만료 정보
- `pdf_access_logs.csv`: PDF 다운로드 기록

CSV 저장소는 시작 시 누락된 파일을 만들고, 기존 `users.csv`의 레거시 `roles` 스키마를 현재 `role` 스키마로 마이그레이션합니다. 쓰기 작업은 잠금 안에서 처리하며, 실패 시 트랜잭션 시작 시점으로 복원합니다.

## 역할

| 역할 | 메뉴 |
|---|---|
| 비로그인 | 책 둘러보기, 로그인, 회원가입 |
| `USER` | 책 둘러보기, 내 대여, 책 등록, 내 등록 도서 |
| `ADMIN` | 책 둘러보기, 관리자 대시보드, 도서 승인, 대여 승인, 전체 대출, 사용자 관리, 데이터 관리 |

PDF 자료는 실물 대여 흐름에 들어가지 않습니다. 승인된 PDF는 활성 `USER`와 `ADMIN`이 다운로드할 수 있고, 다운로드 이력은 `pdf_access_logs.csv`에 기록됩니다.

## 관리자 CLI

```bash
# 관리자 생성
python -m book_rental.admin_command_runner create-admin

# 로그인/비밀번호 해시 진단
python -m book_rental.admin_command_runner debug-login --military-id 333

# 기존 활성 PDF 대출 정리 대상 확인
python -m book_rental.admin_command_runner migrate-pdf-loans --dry-run

# 기존 활성 PDF 대출을 RETURNED로 마이그레이션
python -m book_rental.admin_command_runner migrate-pdf-loans --apply
```

별도 데이터 경로를 사용할 때는 각 명령에 `--data-dir /path/to/data`를 추가할 수 있습니다.

## 테스트

```bash
pip install -r requirements-dev.txt
pytest -q
```

테스트는 인증, 세션 유지, 도서 등록/승인, 실물 대여 생명주기, PDF 다운로드, 관리자 데이터 관리, CSV 마이그레이션을 포함합니다.

## 구조

```text
app.py                              # Streamlit UI와 역할별 메뉴
book_rental/auth.py                 # 비밀번호 해시/검증
book_rental/bootstrap.py            # 개발용 관리자 자동 생성
book_rental/config.py               # 데이터 디렉터리 설정
book_rental/service.py              # 인증, 권한, 도서/대여 업무 규칙
book_rental/sessions.py             # 15분 로그인 유지 세션
book_rental/store.py                # CSV 스키마, 마이그레이션, 잠금, 원자적 저장
book_rental/admin_data.py           # 관리자 CSV 관리 서비스
book_rental/admin_command_runner.py # 관리자/진단/마이그레이션 CLI
tests/                              # pytest 테스트
data/                               # 기본 CSV 데이터와 uploads/
```
