# BookBridge

Streamlit과 CSV 파일 저장소로 구현한 회원가입·로그인 기반 책 대여 플랫폼입니다. 로그인하지 않은 방문자도 승인된 도서를 둘러볼 수 있고, 일반 회원은 하나의 계정으로 도서 등록과 대여를 모두 이용할 수 있습니다.

## 주요 기능

- 군번을 로그인 ID로 사용하는 회원가입·로그인 및 로그아웃
- PBKDF2-SHA256 기반 비밀번호 해시 저장(평문 비밀번호 미저장)
- 비로그인 사용자도 승인 도서의 제목, 저자, 카테고리, 수량, PDF 여부 조회 가능
- 일반 회원(`USER`)의 책 등록, 내 등록 도서, 대여 요청, 내 대여 통합 이용
- 관리자(`ADMIN`) 전용 도서 승인, 대여 승인, 전체 대출, 사용자 관리, 대시보드
- 승인된 대여의 재고 차감, 반납 시 재고 복구, 연체 상태 자동 동기화
- 대여 중인 사용자와 관리자만 승인된 PDF 다운로드 가능
- 기존 `users.csv`의 `roles`/`email` 스키마를 신규 인증 스키마로 자동 마이그레이션

## 로컬 실행

Python 3.11 이상을 권장합니다.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 `http://localhost:8501`을 엽니다. 최초 실행 시 데모 사용자는 자동 생성되지 않습니다. 아래 명령으로 관리자 계정을 먼저 생성하거나 초기 화면에서 일반 회원가입을 진행하세요.

다른 데이터 디렉터리를 사용하려면 다음과 같이 지정합니다.

```bash
BOOKBRIDGE_DATA_DIR=/path/to/data streamlit run app.py
```

## 관리자 계정 생성

관리자는 일반 회원가입 화면에서 만들 수 없습니다. 관리자 비밀번호는 소스 코드에 넣지 말고 명령행 인자 또는 환경변수로 전달하세요.

### 명령행 인자 사용

```bash
python -m book_rental.admin_command_runner create-admin \
  --military-id admin \
  --password '안전한-비밀번호' \
  --name 관리자
```

별도 데이터 디렉터리를 사용하는 경우 `--data-dir /path/to/data`를 추가합니다. 같은 군번의 관리자 계정이 이미 있으면 새 계정을 만들거나 비밀번호를 덮어쓰지 않고 안내 메시지만 출력합니다.

### 환경변수 사용

```bash
export BOOKBRIDGE_ADMIN_ID=admin
export BOOKBRIDGE_ADMIN_PASSWORD='안전한-비밀번호'
export BOOKBRIDGE_ADMIN_NAME=관리자
# 선택 사항: export BOOKBRIDGE_DATA_DIR=/path/to/data
python -m book_rental.admin_command_runner create-admin
```

운영 환경에서는 셸 히스토리에 비밀번호가 남지 않도록 환경변수 또는 별도의 비밀 관리 도구 사용을 권장합니다.

## 역할과 권한

| 로그인 상태/역할 | 이용 가능한 메뉴 |
|---|---|
| 비로그인 | 책 둘러보기, 로그인, 회원가입 |
| `USER` | 책 둘러보기, 내 대여, 책 등록, 내 등록 도서 |
| `ADMIN` | 책 둘러보기, 관리자 대시보드, 도서 승인, 대여 승인, 전체 대출, 사용자 관리 |

일반 회원은 등록자와 대여자 역할을 따로 선택하거나 전환하지 않습니다. 하나의 `USER` 계정으로 두 기능을 모두 사용합니다.

## CSV 데이터와 마이그레이션

기본 데이터 디렉터리는 `data/`이며 아래 파일이 테이블 역할을 합니다.

- `users.csv`: `id,name,military_id,password_hash,role,active,created_at,updated_at`
- `books.csv`
- `borrow_requests.csv`
- `loans.csv`
- `admin_logs.csv`

기존 `users.csv`에 `military_id`, `password_hash`, `role` 컬럼이 없어도 앱 시작 시 새 스키마로 안전하게 다시 기록합니다. 기존 `ADMIN`은 `ADMIN`으로, 기존 `LENDER`/`BORROWER`는 `USER`로 매핑됩니다. 다만 기존 계정에는 비밀번호와 군번 정보가 없으므로 로그인할 수 없습니다. 필요한 운영 계정은 관리자 생성 명령 또는 신규 회원가입으로 생성해야 합니다.

쓰기 작업은 프로세스 잠금으로 직렬화하고, 임시 파일을 쓴 뒤 원본 파일을 교체합니다. 여러 CSV를 변경하는 처리 중 오류가 발생하면 트랜잭션 시작 시점의 백업으로 복원합니다. CSV 방식은 로컬·소규모 운영에 적합하며 여러 서버 인스턴스에서 공유하는 운영 환경에는 관계형 데이터베이스가 더 적합합니다.

## 테스트

```bash
pip install -r requirements-dev.txt
pytest -q
```

테스트는 회원가입, 중복 군번, 비밀번호 확인, 로그인, 관리자 권한, 일반 회원의 등록·대여 통합 권한, PDF 다운로드 권한, 기존 CSV 마이그레이션을 포함합니다.

## 수동 확인 시나리오

1. 빈 데이터 디렉터리로 앱을 실행하고 초기 화면에 사용자 선택 드롭다운 없이 `BookBridge`, 회원가입/로그인 버튼, 승인 도서 목록이 표시되는지 확인합니다.
2. 일반 회원가입 후 군번과 비밀번호로 로그인하고 사이드바에 이름/군번과 로그아웃 버튼이 표시되는지 확인합니다.
3. 동일한 일반 계정으로 책을 등록하고, 관리자가 승인한 다른 책에 대여 요청을 보낼 수 있는지 확인합니다.
4. 관리자 계정으로 로그인해 도서 승인, 대여 승인, 전체 대출, 사용자 관리 메뉴만 노출되는지 확인합니다.
5. PDF 책의 대여를 승인한 뒤 해당 회원의 `내 대여`에 다운로드 버튼이 나타나는지 확인합니다.
6. 다른 일반 회원은 해당 PDF를 받을 수 없고, 반납 완료 후 기존 대여자도 다운로드할 수 없는지 확인합니다.
7. 로그아웃 후 보호된 메뉴가 사라지고 승인 도서 목록은 계속 조회되는지 확인합니다.

## 구조

```text
app.py                                  # Streamlit 인증 화면, 역할별 메뉴와 사용자 액션
book_rental/auth.py                     # 비밀번호 해시 생성과 검증
book_rental/admin_command_runner.py     # 별도 관리자 생성 CLI
book_rental/service.py                  # 인증, 권한 및 대여 비즈니스 규칙
book_rental/store.py                    # CSV 스키마 마이그레이션, 잠금, 원자적 저장
book_rental/errors.py                   # 사용자 표시용 도메인 예외
data/                                   # CSV 데이터와 PDF 업로드 디렉터리
tests/test_service.py                   # 인증·권한·대여·마이그레이션 테스트
```

상세 설계는 [`docs/architecture.md`](docs/architecture.md)를 참고하세요.
