# 프로젝트 기능 및 권한 분석

## 1. 분석 개요

- 분석 대상: `app.py`, `book_rental/*.py`, `pyproject.toml`, `requirements*.txt`
- 주요 기술 스택: Streamlit UI(`app.py:5-7`, `requirements.txt:1`), pandas 표 렌더링(`app.py:5`, `app.py:42-49`), CSV 파일 저장소(`book_rental/store.py:15-41`, `book_rental/store.py:44-171`), argparse 기반 관리자 CLI(`book_rental/admin_command_runner.py:3-26`)
- 애플리케이션 진입점:
  - Streamlit 앱: `app.py` 최상위 실행 코드(`app.py:17-462`)
  - 관리자 CLI: `book_rental.admin_command_runner.main()` 및 `if __name__ == "__main__"`(`book_rental/admin_command_runner.py:62-92`)
- 인증 방식: 군번(`military_id`)과 비밀번호를 CSV 사용자 데이터와 대조하고, 비밀번호는 `pbkdf2_sha256` 해시로 검증한다(`book_rental/service.py:94-117`, `book_rental/auth.py:17-69`). 로그인 성공 후 15분 만료 세션 토큰을 발급해 토큰 해시만 `sessions.csv`에 저장한다(`book_rental/login.py:51-76`, `book_rental/sessions.py:10-33`).
- 인가 방식: 문자열 역할 `USER`, `ADMIN`을 직접 비교한다. 일반 서비스는 `BookRentalService.require_role()`을 사용하고(`book_rental/service.py:337-341`), CSV 데이터 관리 기능은 `AdminDataService._require_admin()`을 사용한다(`book_rental/admin_data.py:162-175`). 코드상 역할 계층은 없다.
- 분석에서 제외한 경로: `README.md`, `README.*`, `docs/`, 테스트 전용 기능, 빌드 산출물 및 외부 의존성 디렉터리. 테스트 파일은 구현 보조 확인용 검색 대상이었으나 기능 근거로 문서화하지 않았다.

## 2. 사용자 역할 및 권한

| 역할 또는 권한 | 코드 정의 위치 | 설명 | 실제 사용 여부 |
| --- | --- | --- | --- |
| `USER` | 사용자 CSV 스키마의 `role` 컬럼(`book_rental/store.py:15-19`), 회원가입 생성값(`book_rental/service.py:47-50`), 역할 검증(`book_rental/admin_data.py:63-64`, `book_rental/admin_data.py:114-115`) | 일반 사용자. 책 대여 요청, 본인 대여 조회, 책 등록, 본인 등록 도서 조회가 가능하다. | 사용됨. UI 메뉴 분기(`app.py:119-120`, `app.py:163-167`) 및 서비스 권한 검사(`book_rental/service.py:122-135`, `book_rental/service.py:195-230`, `book_rental/service.py:281-287`)에서 사용된다. |
| `ADMIN` | 사용자 CSV 스키마의 `role` 컬럼(`book_rental/store.py:15-19`), 관리자 생성(`book_rental/service.py:52-62`), 역할 검증(`book_rental/admin_data.py:63-64`, `book_rental/admin_data.py:114-115`) | 관리자. 승인, 전체 조회, 사용자 관리, CSV 데이터 관리가 가능하다. | 사용됨. UI 메뉴 분기(`app.py:121-122`) 및 서비스/관리 데이터 권한 검사(`book_rental/service.py:43-45`, `book_rental/service.py:126-128`, `book_rental/service.py:232-238`, `book_rental/admin_data.py:28-39`)에서 사용된다. |
| legacy `roles` | 사용자 CSV 마이그레이션(`book_rental/store.py:71-77`) | 이전 스키마의 `roles` 값을 읽어 `ADMIN` 포함 시 `ADMIN`, 아니면 `USER`로 변환한다. | 마이그레이션에서만 사용됨. 현재 권한 검사에는 `role`만 사용된다. |
| `LENDER` | 실행 코드에는 권한으로 정의되지 않음. legacy `roles` 변환 입력으로만 언급 가능(`book_rental/store.py:71-77`) | 현재 역할로 유지되지 않고 `USER`로 변환될 수 있다. | 현재 인가에는 사용되지 않음. |

역할 계층:

코드에서 `ADMIN`이 `USER` 권한을 상속한다는 계층 관계는 확인되지 않는다. `require_role(user_id, "USER")`는 `ADMIN`을 허용하지 않고, `require_role(user_id, "ADMIN")`도 `USER`를 허용하지 않는다(`book_rental/service.py:337-341`).

## 3. 전체 기능 목록

| 기능 영역 | 기능 | 설명 | 진입점 | 주요 구현 위치 |
| --- | --- | --- | --- | --- |
| 인증/세션 | 세션 복원 | 브라우저 쿠키 또는 Streamlit 세션의 토큰으로 로그인 상태를 복원하고 만료 시간을 연장한다. | Streamlit 앱 로드 | `app.py:71-94`, `book_rental/sessions.py:35-61` |
| 인증/세션 | 로그인 | 군번/비밀번호 인증 후 세션 토큰을 발급하고 쿠키를 설정한다. | `로그인` 화면 | `app.py:173-214`, `book_rental/login.py:51-76`, `book_rental/service.py:94-117` |
| 인증/세션 | 로그아웃 | 세션 토큰을 폐기하고 UI 상태와 쿠키를 제거한다. | 사이드바 로그아웃 버튼 | `app.py:104-117`, `book_rental/sessions.py:63-71` |
| 사용자 | 회원가입 | 일반 사용자(`USER`) 계정을 생성한다. | `회원가입` 화면 | `app.py:216-235`, `book_rental/service.py:47-92` |
| 도서 | 승인 도서 목록/검색 | 승인된 책만 조회하고 제목/저자/카테고리로 필터링한다. | `책 둘러보기` 화면 | `app.py:136-171`, `book_rental/service.py:119-120` |
| 도서/대여 | 대여 요청 | 일반 사용자가 승인된 책에 대해 수량을 지정해 대여 요청을 만든다. | `책 둘러보기`의 `대여 요청` 버튼 | `app.py:163-167`, `book_rental/service.py:195-225` |
| 대여 | 내 대여 조회 | 본인 대여 요청과 대출 현황을 조회한다. | `내 대여` 화면 | `app.py:240-246`, `book_rental/service.py:227-230`, `book_rental/service.py:281-287` |
| 대여 | PDF 다운로드 | 본인 또는 관리자가 대여 중인 PDF 책 파일을 다운로드한다. | `내 대여`, `전체 대출` 화면 | `app.py:247-258`, `app.py:353-358`, `book_rental/service.py:289-304` |
| 대여 | 반납 처리 | 대여자 또는 관리자가 대여 중/연체 대출을 반납 처리하고 재고를 복구한다. | `내 대여`, `전체 대출` 화면 | `app.py:259-263`, `app.py:359-363`, `book_rental/service.py:306-321` |
| 도서 등록 | 책 등록 | 일반 사용자가 실물 도서 또는 PDF 책을 승인 대기 상태로 등록한다. | `책 등록` 화면 | `app.py:265-307`, `book_rental/service.py:130-169` |
| 도서 등록 | 내 등록 도서 조회 | 일반 사용자가 본인이 등록한 책 목록을 조회한다. | `내 등록 도서` 화면 | `app.py:309-311`, `book_rental/service.py:122-124` |
| 관리자 | 관리자 대시보드 | 사용자, 책, 요청, 대출 상태 건수를 집계한다. | `관리자 대시보드` 화면 | `app.py:313-320`, `book_rental/service.py:323-335` |
| 관리자 | 도서 승인/거절 | 승인 대기 책을 승인 또는 거절하고 관리자 로그를 남긴다. | `도서 승인` 화면 | `app.py:322-333`, `book_rental/service.py:126-128`, `book_rental/service.py:171-193` |
| 관리자 | 대여 요청 승인/거절 | 대여 요청을 승인하면 대출을 만들고 재고를 차감한다. 거절 시 사유를 기록한다. | `대여 승인` 화면 | `app.py:335-347`, `book_rental/service.py:232-279` |
| 관리자 | 전체 대출 관리 | 모든 대출을 조회하고 PDF 확인 및 반납 처리를 수행한다. | `전체 대출` 화면 | `app.py:349-363`, `book_rental/service.py:281-321` |
| 관리자 | 사용자 관리 | 사용자 목록을 조회하고 일반 사용자 계정을 추가한다. | `사용자 관리` 화면 | `app.py:365-376`, `book_rental/service.py:43-68` |
| 관리자 | CSV 데이터 관리 | users/books/borrow_requests/loans CSV를 편집하고 admin_logs를 조회한다. 백업과 변경 로그를 생성한다. | `데이터 관리` 화면 | `app.py:378-462`, `book_rental/admin_data.py:13-180` |
| 관리자 CLI | 관리자 계정 생성 | 로컬 CLI에서 `ADMIN` 계정을 생성하거나 기존 관리자 계정을 확인한다. | `create-admin` 명령 | `book_rental/admin_command_runner.py:15-25`, `book_rental/admin_command_runner.py:62-88`, `book_rental/service.py:52-62` |
| 진단 CLI | 로그인 진단 | 로컬 CLI에서 특정 군번의 사용자 존재 여부, 활성 상태, 역할, 해시 포맷, 비밀번호 검증 결과를 확인한다. | `debug-login` 명령 | `book_rental/admin_command_runner.py:23-25`, `book_rental/admin_command_runner.py:35-59` |

## 4. 권한별 기능 매트릭스

| 기능 | 비로그인 | `USER` | `ADMIN` | 추가 조건 | 근거 코드 |
| --- | --- | --- | --- | --- | --- |
| 승인 도서 목록/검색 | 가능 | 가능 | 가능 | 책 상태가 `APPROVED`인 행만 표시 | `app.py:136-171`, `book_rental/service.py:119-120` |
| 회원가입 | 가능 | 가능 | 가능 | 생성 역할은 `USER`; 동일 군번 금지, 비밀번호 8자 이상 | `app.py:216-235`, `book_rental/service.py:47-92` |
| 로그인 | 가능 | 가능 | 가능 | 활성 계정, 비밀번호 일치 필요 | `app.py:173-214`, `book_rental/service.py:94-117` |
| 로그아웃 | 해당 없음 | 가능 | 가능 | 세션 토큰이 있으면 폐기 | `app.py:104-117`, `book_rental/sessions.py:63-71` |
| 대여 요청 | 불가 | 가능 | 불가 | 승인 도서, 재고 충분, 같은 책의 요청/활성 대출 중복 금지 | `app.py:163-167`, `book_rental/service.py:195-225`, `book_rental/service.py:337-341` |
| 내 대여 조회 | 불가 | 조건부 | 불가 | 본인 요청/대출만 조회 | `app.py:240-246`, `book_rental/service.py:227-230`, `book_rental/service.py:281-287` |
| 본인 PDF 다운로드 | 불가 | 조건부 | 조건부 | `LOANED` 또는 `OVERDUE` 상태의 PDF. `USER`는 본인 대출만, `ADMIN`은 모든 대출 가능 | `book_rental/service.py:289-304` |
| 본인 반납 처리 | 불가 | 조건부 | 조건부 | `LOANED` 또는 `OVERDUE`; `USER`는 본인 대출만, `ADMIN`은 모든 대출 가능 | `book_rental/service.py:306-321` |
| 책 등록 | 불가 | 가능 | 불가 | 필수값, 수량/대여일 1 이상, PDF는 파일 필요 | `app.py:265-307`, `book_rental/service.py:130-169` |
| 내 등록 도서 조회 | 불가 | 조건부 | 불가 | 본인이 lender인 책만 조회 | `app.py:309-311`, `book_rental/service.py:122-124` |
| 관리자 대시보드 | 불가 | 불가 | 가능 | 활성 관리자 필요 | `app.py:313-320`, `book_rental/service.py:323-341` |
| 도서 승인/거절 | 불가 | 불가 | 조건부 | 책 상태가 `PENDING`; 거절은 메모 필요 | `app.py:322-333`, `book_rental/service.py:171-193` |
| 대여 승인/거절 | 불가 | 불가 | 조건부 | 요청 상태가 `REQUESTED`; 승인 시 책 `APPROVED` 및 재고 충분; 거절은 메모 필요 | `app.py:335-347`, `book_rental/service.py:236-279` |
| 전체 대출 조회 | 불가 | 불가 | 가능 | 활성 관리자 필요 | `app.py:349-352`, `book_rental/service.py:281-287` |
| 전체 대출 PDF 확인 | 불가 | 불가 | 조건부 | PDF이며 `LOANED` 또는 `OVERDUE` | `app.py:353-358`, `book_rental/service.py:289-304` |
| 관리자 반납 처리 | 불가 | 불가 | 조건부 | `LOANED` 또는 `OVERDUE` | `app.py:359-363`, `book_rental/service.py:306-321` |
| 사용자 목록 조회 | 불가 | 불가 | 가능 | 활성 관리자 필요, `password_hash` 제외 | `app.py:365-367`, `book_rental/service.py:43-45` |
| 일반 사용자 추가 | 불가 | 불가 | 가능 | 생성 역할은 `USER` | `app.py:368-376`, `book_rental/service.py:64-68` |
| CSV 데이터 조회 | 불가 | 불가 | 가능 | 활성 관리자 필요; `users` 조회 시 `password_hash` 마스킹 | `app.py:378-395`, `book_rental/admin_data.py:28-34`, `book_rental/admin_data.py:162-175` |
| CSV 데이터 편집 | 불가 | 불가 | 조건부 | `users`, `books`, `borrow_requests`, `loans`만 저장 가능; `admin_logs`는 조회 전용 | `app.py:396-426`, `book_rental/admin_data.py:36-55` |
| 데이터 관리에서 사용자 생성/비밀번호 재설정 | 불가 | 불가 | 가능 | `USER` 또는 `ADMIN` 생성 가능, 비밀번호 8자 이상 | `app.py:427-459`, `book_rental/admin_data.py:56-95` |
| 관리자 CLI `create-admin` | 확인 불가 | 확인 불가 | 확인 불가 | 애플리케이션 세션/역할 검사 없음. 로컬 CLI 실행 권한과 인자/환경변수에 의존 | `book_rental/admin_command_runner.py:62-88`, `book_rental/service.py:52-62` |
| 진단 CLI `debug-login` | 확인 불가 | 확인 불가 | 확인 불가 | 애플리케이션 세션/역할 검사 없음. 로컬 CLI 실행자가 대상 군번과 비밀번호 입력으로 진단 | `book_rental/admin_command_runner.py:35-59` |

## 5. 기능 상세

### 세션 복원 및 로그아웃

- 기능 설명: 앱 시작 시 `bookbridge_session` 쿠키 또는 `st.session_state.session_token`을 읽어 사용자 세션을 복원한다. 로그아웃 시 토큰을 폐기한다.
- 진입점: Streamlit 앱 로드, 사이드바 로그아웃 버튼
- 인증 필요 여부: 복원은 토큰 필요, 로그아웃은 현재 UI 사용자 상태 필요
- 허용 역할 또는 권한: 토큰에 연결된 활성 사용자. 역할은 세션 저장값과 현재 사용자 역할이 일치해야 한다.
- 추가 접근 조건: 세션이 만료되지 않았고 `revoked_at`이 비어 있어야 한다.
- 주요 처리 흐름: Streamlit 앱 로드 -> 쿠키/세션 토큰 조회 -> `SessionService.restore()` -> `CsvStore.read("sessions")`/`read_users()` -> `st.session_state.user` 저장. 로그아웃은 버튼 -> `SessionService.revoke()` -> 세션/쿠키 제거.
- 관련 코드: `app.py:71-117`, `book_rental/sessions.py:35-71`, `book_rental/store.py:107-133`
- 비고: 쿠키는 Streamlit 컴포넌트 JS로 설정되며 HttpOnly 속성은 코드상 사용되지 않는다(`app.py:57-68`).

### 로그인

- 기능 설명: 군번과 비밀번호를 검증하고 성공 시 세션 토큰을 만든다.
- 진입점: `로그인` 화면 폼 제출
- 인증 필요 여부: 비로그인 사용자가 수행하는 인증 기능
- 허용 역할 또는 권한: 활성 계정이면 `USER`, `ADMIN` 모두 로그인 가능
- 추가 접근 조건: 계정 존재, 활성 상태, 비밀번호 일치
- 주요 처리 흐름: Login form -> `attempt_login()` -> `BookRentalService.authenticate()` -> `verify_password()` -> `SessionService.create()` -> `st.session_state.user`/쿠키 저장
- 관련 코드: `app.py:173-214`, `book_rental/login.py:51-76`, `book_rental/service.py:94-117`, `book_rental/auth.py:31-69`, `book_rental/sessions.py:20-33`
- 비고: 인증 실패 상태는 `ACCOUNT_NOT_FOUND`, `INVALID_PASSWORD`, `ACCOUNT_INACTIVE`로 구분된다(`book_rental/service.py:102-107`).

### 회원가입

- 기능 설명: 새 일반 사용자 계정을 생성한다.
- 진입점: `회원가입` 화면 폼 제출
- 인증 필요 여부: 불필요
- 허용 역할 또는 권한: 비로그인 포함 누구나 UI에서 접근 가능
- 추가 접근 조건: 이름/군번 필수, 비밀번호 확인 일치, 8자 이상, 군번 중복 금지
- 주요 처리 흐름: Signup form -> `BookRentalService.register_user()` -> `_create_user(..., "USER")` -> `CsvStore.transaction()` -> `users.csv` 저장
- 관련 코드: `app.py:216-235`, `book_rental/service.py:47-92`, `book_rental/auth.py:17-28`
- 비고: 생성되는 역할은 항상 `USER`다.

### 승인 도서 목록 및 검색

- 기능 설명: `APPROVED` 상태의 책을 표시하고 검색어로 제목/저자/카테고리를 필터링한다.
- 진입점: `책 둘러보기` 화면
- 인증 필요 여부: 불필요
- 허용 역할 또는 권한: 비로그인, `USER`, `ADMIN`
- 추가 접근 조건: 책 상태가 `APPROVED`
- 주요 처리 흐름: `책 둘러보기` -> `BookRentalService.approved_books()` -> `CsvStore.read("books")` -> `_enrich_books()`
- 관련 코드: `app.py:136-171`, `book_rental/service.py:119-120`, `book_rental/service.py:373-378`
- 비고: 비로그인 사용자는 대여 버튼 대신 로그인 안내만 본다(`app.py:170-171`).

### 대여 요청

- 기능 설명: 일반 사용자가 승인된 책의 대여를 요청한다.
- 진입점: `책 둘러보기`의 `대여 요청` 버튼
- 인증 필요 여부: 필요
- 허용 역할 또는 권한: `USER`
- 추가 접근 조건: 책 상태 `APPROVED`, 요청 수량 1 이상, 재고 충분, 같은 사용자/책의 대기 요청 또는 활성 대출 중복 금지
- 주요 처리 흐름: Browse UI -> `BookRentalService.create_borrow_request()` -> `require_role(..., "USER")` -> 책/요청/대출 CSV 확인 -> `borrow_requests.csv` 저장
- 관련 코드: `app.py:163-167`, `book_rental/service.py:195-225`, `book_rental/service.py:337-341`
- 비고: `ADMIN`은 `require_role(..., "USER")`에서 차단된다.

### 내 대여, PDF 다운로드, 반납

- 기능 설명: 일반 사용자가 본인의 대여 요청과 대출을 조회하고, 대여 중 PDF를 다운로드하며, 대여 중/연체 상태의 대출을 반납한다.
- 진입점: `내 대여` 화면
- 인증 필요 여부: 필요
- 허용 역할 또는 권한: 조회는 `USER`; PDF 다운로드/반납은 `USER` 본인 또는 `ADMIN`
- 추가 접근 조건: 조회는 본인 `borrower_id`; PDF는 책 형식 `PDF` 및 대출 상태 `LOANED`/`OVERDUE`; 반납은 상태 `LOANED`/`OVERDUE`
- 주요 처리 흐름: `내 대여` -> `borrower_requests()`/`loans(admin=False)` -> `require_role(..., "USER")` -> CSV 조회. PDF는 `pdf_download()` -> 사용자 활성/역할/borrower 검사 -> 파일 읽기. 반납은 `return_book()` -> borrower 또는 관리자 검사 -> 재고 증가 및 대출 상태 변경.
- 관련 코드: `app.py:240-263`, `book_rental/service.py:227-230`, `book_rental/service.py:281-321`
- 비고: `return_book()`은 서비스 메서드 내부에서 사용자 `active` 상태를 확인하지 않는다. UI 로그인/세션 흐름은 활성 사용자만 세션화하지만, 서비스 직접 호출 기준으로는 불명확하다(`book_rental/service.py:306-321`).

### 책 등록 및 내 등록 도서

- 기능 설명: 일반 사용자가 책을 `PENDING` 상태로 등록하고, 본인이 등록한 책 목록을 조회한다.
- 진입점: `책 등록`, `내 등록 도서` 화면
- 인증 필요 여부: 필요
- 허용 역할 또는 권한: `USER`
- 추가 접근 조건: 제목/저자/카테고리 필수, 수량/대여일 1 이상, `PHYSICAL_BOOK` 또는 `PDF`, PDF는 업로드 파일 필요 및 확장자 `.pdf`
- 주요 처리 흐름: `책 등록` -> `BookRentalService.create_book()` -> `require_role(..., "USER")` -> 필요 시 PDF 파일 저장 -> `books.csv` 저장. `내 등록 도서` -> `lender_books()` -> 본인 `lender_id` 필터.
- 관련 코드: `app.py:265-311`, `book_rental/service.py:122-169`
- 비고: 등록 직후에는 대여 목록에 노출되지 않고 관리자 승인이 필요하다.

### 관리자 대시보드

- 기능 설명: 사용자/책/요청/대출 상태 건수를 집계한다.
- 진입점: `관리자 대시보드` 화면
- 인증 필요 여부: 필요
- 허용 역할 또는 권한: `ADMIN`
- 추가 접근 조건: 활성 관리자
- 주요 처리 흐름: Admin page -> `BookRentalService.dashboard()` -> `require_role(..., "ADMIN")` -> `_sync_overdue()` -> CSV 집계
- 관련 코드: `app.py:313-320`, `book_rental/service.py:323-352`, `book_rental/service.py:337-341`
- 비고: 연체 동기화가 조회 중 수행될 수 있다.

### 도서 승인/거절

- 기능 설명: 관리자가 `PENDING` 책을 승인 또는 거절한다.
- 진입점: `도서 승인` 화면
- 인증 필요 여부: 필요
- 허용 역할 또는 권한: `ADMIN`
- 추가 접근 조건: 책 상태 `PENDING`; 거절 시 메모 필수
- 주요 처리 흐름: Admin page -> `pending_books()` -> `require_role(..., "ADMIN")` -> 승인/거절 버튼 -> `approve_book()` 또는 `reject_book()` -> 상태 변경 -> `_log()`
- 관련 코드: `app.py:322-333`, `book_rental/service.py:126-128`, `book_rental/service.py:171-193`, `book_rental/service.py:354-361`
- 비고: 승인/거절 모두 관리자 로그에 남는다.

### 대여 요청 승인/거절

- 기능 설명: 관리자가 모든 대여 요청을 조회하고 `REQUESTED` 요청을 승인 또는 거절한다. 승인 시 대출을 생성하고 책 재고를 차감한다.
- 진입점: `대여 승인` 화면
- 인증 필요 여부: 필요
- 허용 역할 또는 권한: `ADMIN`
- 추가 접근 조건: 요청 상태 `REQUESTED`; 승인 시 책 상태 `APPROVED` 및 재고 충분; 거절 시 메모 필수
- 주요 처리 흐름: Admin page -> `all_requests()` -> `require_role(..., "ADMIN")` -> `approve_request()`/`reject_request()` -> 요청 상태 변경 -> 필요 시 `loans.csv` 생성 및 책 재고 차감 -> `_log()`
- 관련 코드: `app.py:335-347`, `book_rental/service.py:232-279`, `book_rental/service.py:354-361`
- 비고: 승인 처리 중 책/요청/대출 CSV를 같은 트랜잭션에서 갱신한다(`book_rental/service.py:236-265`).

### 전체 대출 관리

- 기능 설명: 관리자가 전체 대출을 조회하고, PDF를 확인하며, 대출을 반납 처리한다.
- 진입점: `전체 대출` 화면
- 인증 필요 여부: 필요
- 허용 역할 또는 권한: `ADMIN`
- 추가 접근 조건: 전체 조회는 활성 관리자. PDF/반납은 대여 상태 조건이 추가된다.
- 주요 처리 흐름: Admin page -> `loans(admin=True)` -> `require_role(..., "ADMIN")` -> 전체 대출 조회. PDF는 `pdf_download()`, 반납은 `return_book()`으로 처리.
- 관련 코드: `app.py:349-363`, `book_rental/service.py:281-321`
- 비고: `return_book()`의 활성 사용자 검사 누락 가능성은 7장에 별도 기록했다.

### 사용자 관리

- 기능 설명: 관리자가 사용자 목록을 보고 일반 사용자 계정을 추가한다.
- 진입점: `사용자 관리` 화면
- 인증 필요 여부: 필요
- 허용 역할 또는 권한: `ADMIN`
- 추가 접근 조건: 활성 관리자, 생성 계정은 `USER`
- 주요 처리 흐름: Admin page -> `users()` -> `require_role(..., "ADMIN")` -> password_hash 제외 목록 반환. 사용자 추가 -> `admin_create_user()` -> `require_role(..., "ADMIN")` -> `_create_user(..., "USER")`
- 관련 코드: `app.py:365-376`, `book_rental/service.py:43-68`, `book_rental/service.py:337-341`
- 비고: 이 화면에서는 관리자 계정을 만들 수 없다. 관리자 계정 생성은 데이터 관리 또는 CLI에서 가능하다.

### CSV 데이터 관리

- 기능 설명: 관리자가 CSV 테이블을 조회/편집하고, 변경 전 백업 및 관리자 로그를 남긴다. `admin_logs`는 조회 전용이다.
- 진입점: `데이터 관리` 화면
- 인증 필요 여부: 필요
- 허용 역할 또는 권한: `ADMIN`
- 추가 접근 조건: 활성 관리자. 저장 가능 테이블은 `users`, `books`, `borrow_requests`, `loans`이며 `admin_logs`는 저장 불가. `users.role`은 `USER` 또는 `ADMIN`만 허용된다.
- 주요 처리 흐름: Admin data page -> UI role guard -> `AdminDataService.read_table()`/`save_table()`/`create_user()`/`reset_password()` -> `_require_admin()` -> `_normalize_and_validate()` -> `_backup()` -> `CsvStore.write()` -> `_append_log()`
- 관련 코드: `app.py:378-462`, `book_rental/admin_data.py:13-180`, `book_rental/store.py:15-41`
- 비고: `users` 조회 시 `password_hash`는 마스킹되고, 저장 시 기존 마스킹값은 기존 해시로 복원된다(`book_rental/admin_data.py:28-50`).

### 관리자 CLI

- 기능 설명: 로컬 명령으로 관리자 계정을 생성하거나 로그인 관련 진단을 수행한다.
- 진입점: `book_rental.admin_command_runner.main()`
- 인증 필요 여부: 애플리케이션 인증 없음
- 허용 역할 또는 권한: 코드상 앱 역할 검사 없음
- 추가 접근 조건: `create-admin`은 군번/비밀번호/이름 인자 또는 환경변수가 필요하다. `debug-login`은 군번과 프롬프트 비밀번호가 필요하다.
- 주요 처리 흐름: CLI args -> `resolve_data_dir()` -> `CsvStore` -> `BookRentalService.create_admin()` 또는 `debug_login()` -> CSV 읽기/쓰기 또는 비밀번호 검증
- 관련 코드: `book_rental/admin_command_runner.py:15-92`, `book_rental/service.py:52-62`, `book_rental/auth.py:57-69`
- 비고: CLI 실행 자체에 대한 인증/인가 구현은 코드에서 확인되지 않는다. OS/배포 환경 권한에 의존하는 것으로만 확인된다.

## 6. 인증 및 인가 처리 구조

- 로그인 및 토큰 발급 과정: 로그인 폼 제출 시 `attempt_login()`이 `BookRentalService.authenticate()`를 호출한다(`app.py:173-181`, `book_rental/login.py:51-60`). 인증 성공 시 `SessionService.create()`가 48바이트 URL-safe 토큰을 만들고 SHA-256 해시를 `sessions.csv`에 저장한다(`book_rental/login.py:62-76`, `book_rental/sessions.py:20-33`).
- 비밀번호 처리: 저장 시 `hash_password()`가 `pbkdf2_sha256$iterations$salt$digest` 형식을 생성하고, 검증 시 `verify_password()`가 `hmac.compare_digest()`를 사용한다(`book_rental/auth.py:17-69`).
- 세션 또는 토큰 검증 과정: 앱 로드 시 `st.session_state.session_token` 또는 `st.context.cookies[bookbridge_session]`를 읽고 `SessionService.restore()`를 호출한다(`app.py:71-94`). `restore()`는 토큰 해시 일치, 미폐기, 만료 전, 사용자 존재, 활성 상태, 세션 역할과 현재 사용자 역할 일치를 확인한다(`book_rental/sessions.py:35-61`).
- 사용자 정보가 요청 컨텍스트에 저장되는 방식: Streamlit의 `st.session_state.user`에 `id`, `name`, `military_id`, `role`, `active`, 생성/수정 시각을 저장한다(`app.py:80-82`, `app.py:100-102`, `book_rental/login.py:79-95`, `book_rental/sessions.py:57-61`).
- 역할 또는 권한 확인 방식: `BookRentalService.require_role(user_id, role)`가 사용자 조회 후 활성 상태와 역할의 정확한 일치를 검사한다(`book_rental/service.py:337-341`). `AdminDataService._require_admin(actor)`는 actor 객체의 role을 대문자 정규화해 `ADMIN`인지 확인하고 active도 검사한다(`book_rental/admin_data.py:162-175`).
- 리소스 소유권 확인 방식: 본인 등록 도서는 `lender_id == actor_id`로 필터링한다(`book_rental/service.py:122-124`). 본인 요청/대출은 `borrower_id == actor_id`로 필터링한다(`book_rental/service.py:227-230`, `book_rental/service.py:281-287`). PDF 다운로드와 반납은 `ADMIN`이 아니면 `borrower_id == actor_id`여야 한다(`book_rental/service.py:289-321`).
- 인증 실패 및 권한 부족 시 응답 방식: 서비스는 `AuthorizationError`, `ValidationError`, `NotFoundError`를 발생시키고(`book_rental/errors.py:1-14`), UI는 `BookRentalError`를 잡아 `st.error()`로 표시한다(`app.py:30-39`, `app.py:231-235`, `app.py:303-307`, `app.py:461-462`). 로그인 실패는 상태별 메시지를 표시한다(`app.py:207-214`).

## 7. 권한 검사가 불명확하거나 누락된 기능

| 기능 또는 진입점 | 현재 확인된 보호 장치 | 문제 또는 불명확한 점 | 근거 코드 |
| --- | --- | --- | --- |
| `BookRentalService.return_book()` | `ADMIN`이 아니면 `borrower_id == actor_id` 검사, 대출 상태 검사 | 서비스 메서드 자체는 사용자 `active` 상태를 확인하지 않는다. UI 로그인/세션 복원은 활성 사용자만 통과시키지만, 서비스 직접 호출 기준으로는 비활성 사용자 차단 여부가 불명확하다. | `book_rental/service.py:306-321`, 활성 검사 비교: `book_rental/service.py:337-341`, `book_rental/service.py:289-295` |
| 관리자 CLI `create-admin` | 군번/비밀번호/이름 인자 또는 환경변수 필요, 군번 중복 검사 | 애플리케이션 세션이나 기존 관리자 역할 검사가 없다. 로컬 CLI 접근 권한으로 보호되는 운영 도구로 보이나, 코드만으로 실행자 권한 조건은 확인할 수 없다. | `book_rental/admin_command_runner.py:62-88`, `book_rental/service.py:52-62` |
| 진단 CLI `debug-login` | 대상 군번 필요, 비밀번호는 프롬프트 입력 | 앱 인증/인가 없이 사용자 존재, 활성 상태, 역할, 해시 포맷을 출력한다. 로컬 CLI 접근 권한 이외의 보호 장치는 코드에서 확인되지 않는다. | `book_rental/admin_command_runner.py:35-59` |
| `AdminDataService.save_table()`을 통한 CSV 직접 편집 | 활성 `ADMIN` 검사, 테이블 허용 목록, 일부 스키마/상태/수량 검증, 백업/로그 | 관리자는 `books`, `borrow_requests`, `loans`, `users`를 직접 수정할 수 있어 일반 승인/대여 흐름의 세부 상태 전이 규칙을 우회할 수 있다. 이는 관리자 기능으로 구현되어 있으나, 행 단위 리소스 소유권이나 워크플로 전이 검사는 제한적이다. | `app.py:396-426`, `book_rental/admin_data.py:36-55`, `book_rental/admin_data.py:97-127` |
| `SessionService.create()` | 호출자가 전달한 user 객체로 토큰 생성 | 자체적으로 활성 상태나 비밀번호 검증을 하지 않는다. 실제 로그인 흐름에서는 `attempt_login()`이 인증 성공 후에만 호출하지만, 내부 메서드 직접 사용 시 전제 조건은 호출자에게 있다. | `book_rental/login.py:51-76`, `book_rental/sessions.py:20-33` |
| 관리자 화면 UI 분기 | 사이드바 메뉴가 역할별로 페이지를 제한하고, 주요 서비스가 권한을 재검사 | `관리자 대시보드`, `도서 승인`, `대여 승인`, `전체 대출`, `사용자 관리`의 `app.py` 분기 자체에는 별도 role guard가 없고 메뉴 제한에 의존한다. 실제 데이터 접근은 서비스 권한 검사로 보호된다. | UI: `app.py:118-131`, 관리자 분기: `app.py:313-376`, 서비스 검사: `book_rental/service.py:126-341` |

보안 취약점이라고 단정하지 않는다. 위 항목은 코드에서 확인되는 보호 장치와, 코드만으로 확정할 수 없는 실행 환경/직접 호출 조건을 분리해 기록한 것이다.

## 8. 미사용 역할 및 권한

| 역할 또는 권한 | 정의 위치 | 검색 결과 | 비고 |
| --- | --- | --- | --- |
| legacy `roles` | `book_rental/store.py:71-77` | 마이그레이션 입력으로만 사용되고 현재 권한 검사는 `role` 컬럼만 사용한다. | `ADMIN` 포함 여부만 보존되며 그 외 값은 현재 역할로 유지되지 않는다. |
| `LENDER` | 현재 실행 코드의 역할 정의 없음. legacy `roles` 값으로 들어올 수 있음 | 테스트 데이터에서 legacy 예시로만 확인되고, 실행 코드 권한 비교에는 등장하지 않는다. | 현재 스키마에서는 `USER`로 변환될 수 있다(`book_rental/store.py:71-77`). |
| 세부 Permission enum | 없음 | `permission`, `permissions`, 권한 enum 또는 정책 클래스는 실행 코드에서 확인되지 않았다. | 역할 문자열 기반 인가만 확인됨. |

## 9. 분석 한계

- Streamlit은 HTTP 라우터/컨트롤러 기반 프레임워크가 아니므로, 기능 진입점은 `app.py`의 화면 분기와 버튼/폼 이벤트로 추적했다(`app.py:136-462`).
- 배포 환경의 OS 계정, 파일 권한, CLI 실행 제한, Streamlit 서버 설정은 코드에 포함되어 있지 않아 확정할 수 없다. 특히 관리자 CLI 보호 조건은 코드만으로 확인 불가다.
- `data/` 디렉터리의 실제 CSV 내용은 실행 시 상태 데이터이며, 본 분석은 스키마와 코드 흐름 기준으로 작성했다.
- 프론트엔드 메뉴 숨김과 백엔드/서비스 권한 검사를 구분했다. 기능별 실제 차단 근거는 가능한 한 서비스 계층의 `require_role()` 또는 `AdminDataService._require_admin()` 호출로 표시했다.
- 테스트에만 존재하는 동작은 기능으로 문서화하지 않았다.
