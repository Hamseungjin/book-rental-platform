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

### 데이터 디렉터리 설정

앱, `CsvStore()` 기본 생성자, 관리자 생성 명령은 모두 `book_rental/config.py`의 동일한 경로 결정 함수를 사용합니다.

1. `BOOKBRIDGE_DATA_DIR`가 설정되어 있으면 해당 절대 경로를 사용합니다.
2. 설정되어 있지 않으면 현재 실행 디렉터리와 무관하게 **프로젝트 루트의 `data/`**를 사용합니다.

배포 서버에서는 두 CSV 위치가 다시 나뉘지 않도록 한 경로를 명시적으로 선택해 Streamlit 서비스와 관리자 명령에 동일하게 설정해야 합니다. 예를 들어 앱 내부 데이터를 기준으로 통일하려면 다음과 같이 설정합니다.

```bash
export BOOKBRIDGE_DATA_DIR=/opt/bookbridge/app/data
streamlit run /opt/bookbridge/app/app.py
```

루트 데이터 디렉터리를 운영 기준으로 삼으려면 두 명령 모두 `/opt/bookbridge/data`를 사용합니다.

```bash
export BOOKBRIDGE_DATA_DIR=/opt/bookbridge/data
streamlit run /opt/bookbridge/app/app.py
```

현재 사용 중인 절대 경로는 애플리케이션 시작 로그와 관리자 대시보드 상단에서 확인할 수 있습니다.

### systemd 배포 설정 및 확인

Streamlit을 systemd로 실행한다면 셸에서 `export`한 값은 서비스에 자동으로 전달되지 않습니다. 서비스 unit 또는 `EnvironmentFile`에 앱과 관리자 명령이 공유할 데이터 경로를 명시하세요.

```ini
[Service]
WorkingDirectory=/opt/bookbridge/app
Environment="BOOKBRIDGE_DATA_DIR=/opt/bookbridge/app/data"
Environment="BOOKBRIDGE_ADMIN_ID=admin"
Environment="BOOKBRIDGE_ADMIN_NAME=관리자"
# 비밀번호는 예시처럼 unit에 직접 기록하기보다 권한이 제한된 EnvironmentFile 또는 비밀 관리 도구로 전달하세요.
EnvironmentFile=/etc/bookbridge/bookbridge.env
ExecStart=/usr/local/bin/streamlit run /opt/bookbridge/app/app.py --server.address=0.0.0.0 --server.port=80
```

예를 들어 `/etc/bookbridge/bookbridge.env`는 서비스 계정만 읽을 수 있게 만들고 다음 값을 넣습니다.

```bash
BOOKBRIDGE_ADMIN_PASSWORD=안전한-비밀번호
```

설정과 실제 전달 값을 확인하는 명령은 다음과 같습니다.

```bash
systemctl cat <서비스명>
systemctl show <서비스명> -p Environment -p EnvironmentFiles -p ExecStart -p WorkingDirectory
systemctl daemon-reload
systemctl restart <서비스명>
journalctl -u <서비스명> -n 100 --no-pager
```

`/opt/bookbridge/data`를 사용하던 기존 배포를 `/opt/bookbridge/app/data`로 통합할 때는 먼저 서비스를 중지하고 두 디렉터리를 모두 백업한 다음, 운영 기준 CSV와 `uploads/`를 새 경로로 옮기세요. 파일 소유권을 Streamlit 서비스 계정에 맞춘 뒤 `BOOKBRIDGE_DATA_DIR`를 변경하고 서비스를 재시작해야 합니다. 두 디렉터리의 CSV를 단순 덮어쓰기하면 신규 사용자나 도서 데이터가 유실될 수 있으므로 반드시 내용을 비교하고 병합하세요.

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
export BOOKBRIDGE_DATA_DIR=/opt/bookbridge/app/data
cd /opt/bookbridge/app
python3 -m book_rental.admin_command_runner create-admin
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

기본 데이터 디렉터리는 프로젝트 루트의 `data/`입니다. 운영 환경에서는 `BOOKBRIDGE_DATA_DIR`로 앱과 관리자 CLI가 사용할 하나의 절대 경로를 지정하는 것을 권장합니다. 아래 파일이 테이블 역할을 합니다.

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
3. `책 등록`에 처음 진입하자마자 PDF 업로드 버튼이 활성화되어 있고 PDF 파일만 선택 가능한지 확인합니다.
4. 형식을 PDF로 선택하고 파일 없이 `승인 요청`을 눌러 `PDF 파일을 업로드해주세요.`가 표시되며 신청이 생성되지 않는지 확인합니다.
5. PDF를 첨부해 등록하고 `등록 신청이 완료되었습니다.` 메시지와 `확인` 버튼이 표시되는지 확인합니다.
6. `확인`을 누르면 `내 등록 도서`로 이동하며 방금 등록한 도서가 `PENDING` 상태로 한 번만 표시되는지 확인합니다.
7. 관리자 계정으로 로그인해 도서 승인, 대여 승인, 전체 대출, 사용자 관리 메뉴만 노출되는지 확인합니다.
8. PDF 책의 대여를 승인한 뒤 해당 회원의 `내 대여`에 다운로드 버튼이 나타나는지 확인합니다.
9. 다른 일반 회원은 해당 PDF를 받을 수 없고, 반납 완료 후 기존 대여자도 다운로드할 수 없는지 확인합니다.
10. 로그아웃 후 보호된 메뉴가 사라지고 승인 도서 목록은 계속 조회되는지 확인합니다.

## 구조

```text
app.py                                  # Streamlit 인증 화면, 역할별 메뉴와 사용자 액션
book_rental/auth.py                     # 비밀번호 해시 생성과 검증
book_rental/config.py                   # 앱·CLI·Store 공통 데이터 경로 결정
book_rental/admin_command_runner.py     # 별도 관리자 생성 CLI
book_rental/service.py                  # 인증, 권한 및 대여 비즈니스 규칙
book_rental/store.py                    # CSV 스키마 마이그레이션, 잠금, 원자적 저장
book_rental/errors.py                   # 사용자 표시용 도메인 예외
data/                                   # CSV 데이터와 PDF 업로드 디렉터리
tests/test_service.py                   # 인증·권한·대여·마이그레이션 테스트
```

상세 설계는 [`docs/architecture.md`](docs/architecture.md)를 참고하세요.

## 관리자 데이터 관리

`ADMIN` 역할로 로그인하면 사이드바의 **데이터 관리** 메뉴에서 다음 CSV를 관리할 수 있습니다.

- 사용자 관리: `users.csv`
- 도서 관리: `books.csv`
- 대여 요청 관리: `borrow_requests.csv`
- 대출 관리: `loans.csv`
- 관리자 로그 보기: `admin_logs.csv` (조회 전용)

화면 상단에는 앱이 실제 사용하는 데이터 디렉터리가 표시됩니다. 관리 화면은 `/opt/bookbridge/app/data` 또는 `/opt/bookbridge/data`를 하드코딩하지 않으며, 앱·CLI와 동일하게 `BOOKBRIDGE_DATA_DIR` 및 `get_data_dir()`가 결정한 경로만 수정합니다. 일반 사용자는 메뉴를 볼 수 없고 세션 상태를 조작해 접근해도 `권한이 없습니다.` 메시지가 표시됩니다.

편집기는 행 추가·수정·삭제, 저장 전 미리보기, 변경 취소/새로고침을 지원합니다. 행 삭제가 감지되면 별도의 삭제 확인 체크가 필요합니다. `password_hash`는 편집기에서 마스킹되고 읽기 전용이며, 비밀번호 변경은 별도 **비밀번호 재설정** 폼에서만 수행됩니다. 입력한 평문은 PBKDF2 해시로 변환되며 CSV에는 저장되지 않습니다.

### CSV 백업과 안전한 저장

관리자 편집 저장 직전에 현재 파일을 다음 위치에 자동 백업합니다.

```text
${BOOKBRIDGE_DATA_DIR}/backups/<table>_YYYYMMDD_HHMMSS_microseconds.csv
```

저장은 프로세스 공통 `fcntl` 잠금 안에서 최신 CSV를 다시 읽어 처리합니다. 각 CSV는 같은 디렉터리의 임시 파일에 먼저 기록하고 `fsync` 후 `os.replace`로 원자적으로 교체합니다. 여러 CSV를 갱신하는 대여 승인 같은 작업에서 오류가 발생하면 트랜잭션 시작 시점 파일로 전체 복원합니다. 관리자 저장은 필수 컬럼, 숫자 ID와 ID 중복, 군번 중복, 수량 범위, 요청/대출 상태값을 검증한 뒤 수행합니다.

관리자 데이터 추가·수정·삭제 및 비밀번호 재설정은 `admin_logs.csv`에 관리자 ID/이름, 작업 종류, 대상 파일/ID, 작업 시간, 변경 전·후 요약으로 기록됩니다. 비밀번호 해시는 로그 요약에도 노출하지 않습니다.

## 대여 요청과 수량 반영

BookBridge는 **요청 시에는 수량을 차감하지 않고 관리자 승인 시 차감**하는 정책을 사용합니다.

1. 사용자가 대여 요청을 제출하면 잠금 안에서 최신 `books.csv`, `borrow_requests.csv`, `loans.csv`를 다시 읽습니다.
2. 재고 부족, 동일 사용자의 처리 대기 요청 또는 동일 도서의 활성 대출을 검증합니다.
3. 관리자가 승인할 때 최신 재고를 다시 확인합니다.
4. 재고가 충분하면 같은 트랜잭션에서 `books.available_quantity` 감소, 요청 `APPROVED` 변경, `loans.csv` 행 생성을 수행합니다.
5. Streamlit은 성공 메시지를 `st.toast()`와 `st.success()`로 표시한 뒤 `st.rerun()`하여 최신 수량을 즉시 다시 읽습니다.

재고가 0인 도서는 대여 버튼과 수량 입력이 비활성화되고 `대여 가능한 수량이 없습니다.`가 표시됩니다. 동시 승인으로 수량이 부족해지면 후속 승인은 실패하며 요청은 `REQUESTED` 상태로 유지됩니다.

## 15분 로그인 유지

로그인 성공 시 48바이트 이상의 난수 기반 토큰을 만들고 브라우저의 `bookbridge_session` 쿠키에는 토큰 원문만, `sessions.csv`에는 SHA-256 토큰 해시만 저장합니다. 비밀번호와 `password_hash`는 쿠키나 세션 CSV에 저장하지 않습니다.

`sessions.csv` 스키마는 다음과 같습니다.

```text
token_hash,user_id,military_id,role,created_at,expires_at,revoked_at,last_seen_at
```

앱 실행 및 새로고침 시 쿠키 토큰의 해시와 `sessions.csv`를 대조하여 사용자를 복구합니다. 세션은 **활동 시마다 만료 시간이 다시 15분 뒤로 연장되는 sliding expiration** 방식입니다. 마지막 활동 후 15분이 지나면 자동 로그아웃되고 `로그인 세션이 만료되었습니다. 다시 로그인해주세요.`가 표시됩니다. 로그아웃 버튼은 서버 세션의 `revoked_at`을 기록하고 브라우저 쿠키를 삭제합니다.

별도 쿠키 패키지는 추가하지 않았습니다. Streamlit의 `st.context.cookies`로 쿠키를 읽고 동일 출처의 최소 JavaScript 컴포넌트로 토큰 쿠키를 설정·삭제합니다. 쿠키에는 인증 비밀정보가 아닌 폐기 가능한 랜덤 토큰만 저장되며 `SameSite=Lax`, 15분 `Max-Age`, 루트 경로를 사용합니다. 운영 배포에서는 HTTPS 사용을 권장합니다.

## 운영 환경변수

```bash
export BOOKBRIDGE_DATA_DIR=/opt/bookbridge/app/data
# 관리자 생성 CLI에서만 필요
export BOOKBRIDGE_ADMIN_ID=admin
export BOOKBRIDGE_ADMIN_PASSWORD='안전한-비밀번호'
export BOOKBRIDGE_ADMIN_NAME=관리자
streamlit run app.py
```

이번 기능에 새로 추가된 필수 환경변수는 없습니다. `BOOKBRIDGE_DATA_DIR`를 지정하지 않으면 프로젝트 루트의 `data/`를 사용합니다.

## 추가 수동 확인 시나리오

1. 관리자로 로그인해 **데이터 관리**의 다섯 하위 화면과 현재 데이터 디렉터리가 표시되는지 확인합니다.
2. 일반 사용자 로그인 및 세션 상태 조작 상황에서 데이터 관리 메뉴가 숨겨지고 직접 접근 시 권한 오류가 표시되는지 확인합니다.
3. 도서 행을 추가·수정하고 미리보기 후 저장한 다음 `backups/` 백업과 관리자 로그가 생성되는지 확인합니다.
4. 도서 행 삭제 후 확인 체크 없이 저장이 거부되고, 확인 후에는 삭제되는지 확인합니다.
5. 사용자 비밀번호를 재설정한 뒤 CSV에 평문이 없고 새 비밀번호로 로그인되는지 확인합니다.
6. 재고 1권인 도서를 요청하고 관리자가 승인한 직후 목록이 `0 / 1`로 바뀌며 버튼이 비활성화되는지 확인합니다.
7. 같은 책에 대한 중복 요청/활성 대출과 재고 부족 승인이 한국어 오류로 차단되는지 확인합니다.
8. 로그인 후 브라우저를 새로고침해 계정이 복구되는지, 활동 후 만료가 15분 연장되는지 확인합니다.
9. 마지막 활동 후 15분 이상 지난 토큰이 자동 로그인되지 않는지, 로그아웃한 토큰을 다시 넣어도 복구되지 않는지 확인합니다.

## 로그인 오류 진단

로그인은 이제 다음 두 단계를 분리해서 처리합니다.

1. `users.csv`에서 군번, 활성 상태, 비밀번호 해시를 검증하는 기본 인증
2. 인증 성공 후 `sessions.csv`에 15분 유지 토큰을 저장하고 브라우저 쿠키를 설정하는 지속 로그인 처리

존재하지 않는 군번, 비밀번호 불일치, 비활성 계정은 예상 가능한 로그인 실패 결과로 처리합니다. 손상된 `password_hash`, CSV 읽기 오류 등 내부 오류는 사용자에게 상세 정보를 노출하지 않고 `로그인 처리 중 오류가 발생했습니다.`를 표시하며, 서버 로그에는 `logging.exception()`으로 예외 타입과 전체 traceback, 사용 데이터 경로 및 CSV 경로를 기록합니다.

기본 인증이 성공한 뒤 `sessions.csv` 저장이나 쿠키 설정만 실패한 경우에는 현재 Streamlit 세션의 로그인을 유지합니다. 이 경우 서버 로그에 원인을 남기고 사용자에게 새로고침 로그인 유지가 제한될 수 있음을 안내합니다. `sessions.csv`가 없으면 세션 생성 시 현재 스키마로 자동 생성합니다.

`password_hash`는 다음 형식을 엄격하게 파싱합니다.

```text
pbkdf2_sha256$600000$urlsafe-base64-salt$urlsafe-base64-sha256-digest
```

형식 오류와 단순 비밀번호 불일치를 구분하며, 정상 해시는 PBKDF2-SHA256 계산 후 `hmac.compare_digest()`로 비교합니다.

### 서버 CLI 로그인 진단

Streamlit과 같은 데이터 디렉터리 및 `users.csv`를 사용하는지 다음 명령으로 확인할 수 있습니다.

```bash
cd /opt/bookbridge/app
export BOOKBRIDGE_DATA_DIR=/opt/bookbridge/data
python3 -m book_rental.admin_command_runner debug-login --military-id 333
```

명령은 비밀번호를 화면에 표시하지 않는 대화형 입력으로 받으며 다음 항목만 출력합니다.

- 사용 데이터 디렉터리
- 실제 `users.csv` 경로
- 해당 군번 사용자 존재 여부
- 활성 상태와 역할
- `password_hash` 포맷 정상 여부
- 입력한 비밀번호 검증 성공/실패

비밀번호 원문과 전체 `password_hash`는 출력하지 않습니다. CLI 검증 성공 후 `http://13.209.30.31/`에서 군번 `333`으로 로그인하고, 새로고침 후 15분 이내 로그인 유지와 로그아웃을 차례로 확인하세요.

### `LoginResult` ImportError 배포 복구

다음 오류는 `book_rental/login.py`만 새 버전이고 `book_rental/service.py`는 이전 버전인 부분 배포에서 발생합니다.

```text
ImportError: cannot import name 'LoginResult' from 'book_rental.service'
```

현재 `login.py`는 더 이상 `service.LoginResult`를 import하지 않습니다. 이전 서비스의 성공 `dict`/실패 `error` 객체와 현재 서비스의 `status`/`user` 객체를 모두 내부 호환 결과로 정규화합니다. 따라서 이 ImportError 때문에 Streamlit 앱 전체가 시작되지 않는 문제를 방지합니다.

배포 시에는 파일을 개별 복사하지 말고 같은 Git 커밋 전체를 반영한 뒤 서비스를 재시작하세요.

```bash
cd /opt/bookbridge/app
git fetch --all
git checkout <배포-브랜치>
git pull --ff-only
/opt/bookbridge/app/.venv/bin/python -m compileall -q app.py book_rental
sudo systemctl restart <streamlit-service-name>
sudo journalctl -u <streamlit-service-name> -n 100 --no-pager
```

실제 배포 파일에서 의존성이 제거되었는지는 다음 명령으로 확인할 수 있습니다.

```bash
cd /opt/bookbridge/app
/opt/bookbridge/app/.venv/bin/python -c "from book_rental.login import attempt_login; print('login import OK')"
```
