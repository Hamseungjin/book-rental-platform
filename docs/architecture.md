# BookBridge 아키텍처

## 구성

- `app.py`: Streamlit UI, `st.session_state` 로그인 세션, 로그인 상태와 역할별 메뉴 구성
- `book_rental/auth.py`: 무작위 salt와 PBKDF2-SHA256을 사용하는 비밀번호 해시/검증
- `book_rental/config.py`: 앱, 관리자 CLI, 기본 `CsvStore`가 공유하는 데이터 디렉터리 결정
- `book_rental/service.py`: 회원가입·로그인, `USER`/`ADMIN` 권한, 도서·대여 업무 규칙, PDF 접근 제어
- `book_rental/store.py`: CSV 스키마, 레거시 사용자 CSV 마이그레이션, 프로세스 잠금, 원자적 교체와 트랜잭션 복원
- `book_rental/admin_command_runner.py`: 일반 회원가입과 분리된 관리자 계정 생성 진입점

## 데이터 디렉터리

모든 실행 진입점은 `get_data_dir()`를 사용합니다. `BOOKBRIDGE_DATA_DIR`가 있으면 해당 경로를 절대 경로로 정규화하고, 없으면 프로세스의 현재 작업 디렉터리가 아니라 소스 프로젝트 루트의 `data/`를 사용합니다. 따라서 Streamlit 서비스와 관리자 생성 명령에 동일한 환경변수를 설정하면 같은 `users.csv`를 읽고 씁니다. 관리자 대시보드는 현재 경로를 화면에 표시합니다.

## 인증과 역할

`users.csv`는 `id`, `name`, `military_id`, `password_hash`, `role`, `active`, 생성/수정 시각을 저장합니다. 군번은 대소문자를 구분하지 않는 고유 로그인 ID로 검증합니다. 비밀번호 원문은 저장하지 않습니다.

역할은 두 종류입니다.

- `USER`: 도서 등록자와 대여자 기능을 모두 사용
- `ADMIN`: 승인, 전체 현황, 사용자 관리 기능 사용

Streamlit 메뉴 숨김은 사용성을 위한 1차 제어이며, 실제 권한은 모든 보호 서비스 메서드의 `require_role` 호출에서 다시 검증합니다.

## CSV 마이그레이션

저장소 초기화 시 각 CSV 헤더를 현재 스키마와 비교합니다. 레거시 `users.csv`는 행과 ID를 보존하면서 다음과 같이 변환합니다.

- `roles`에 `ADMIN` 포함: `role=ADMIN`
- 그 외 기존 사용자: `role=USER`
- 누락된 `military_id`, `password_hash`: 빈 값

레거시 계정은 인증 정보가 없으므로 자동 로그인 자격을 부여하지 않습니다. 데모 사용자는 더 이상 새 저장소에 시드되지 않습니다.

## PDF 접근 제어

PDF 다운로드는 대출 ID를 기준으로 서버 측에서 다음 조건을 모두 확인합니다.

1. 요청자가 해당 대출의 실제 대여자이거나 관리자일 것
2. 대출 상태가 `LOANED` 또는 `OVERDUE`일 것
3. 책 형식이 `PDF`일 것
4. CSV에 저장된 업로드 경로의 파일이 실제로 존재할 것

검증을 통과한 경우에만 파일 바이트를 Streamlit `st.download_button`에 전달합니다.
