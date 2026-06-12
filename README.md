# BookBridge

Streamlit과 CSV 파일 저장소로 구현한 책 대여 플랫폼입니다. 기존 Spring Boot/MySQL 백엔드와 React 프론트엔드를 하나의 Python 애플리케이션으로 통합했습니다.

## 주요 기능

- 역할 기반 사용자 전환: `BORROWER`, `LENDER`, `ADMIN`
- 책 등록 및 관리자 승인/거절
- 승인된 책 검색과 대여 요청
- 관리자 대여 승인 시 재고 차감 및 대출 생성
- 대여자/관리자 반납 처리와 재고 복구
- 기한이 지난 대출의 연체 상태 자동 동기화
- 관리자 대시보드와 감사 로그
- PDF 책 파일 업로드

## 실행

Python 3.11 이상을 권장합니다.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 `http://localhost:8501`을 엽니다. 최초 실행 시 다음 데모 사용자가 준비됩니다.

| ID | 사용자 | 역할 |
|---:|---|---|
| 1 | 관리자 | ADMIN |
| 2 | 책 등록자 | LENDER |
| 3 | 대여자 | BORROWER |

## CSV 데이터

기본 데이터 디렉터리는 `data/`이며 아래 파일이 테이블 역할을 합니다.

- `users.csv`
- `books.csv`
- `borrow_requests.csv`
- `loans.csv`
- `admin_logs.csv`

다른 경로를 사용하려면 실행 전에 환경 변수를 지정합니다.

```bash
BOOKBRIDGE_DATA_DIR=/path/to/data streamlit run app.py
```

쓰기 작업은 프로세스 잠금으로 직렬화하고, 임시 파일을 쓴 뒤 원본 파일을 교체합니다. 여러 CSV를 변경하는 업무 처리 중 오류가 발생하면 트랜잭션 시작 시점의 백업으로 복원합니다. CSV 방식은 로컬·소규모 운영에 적합하며 여러 서버 인스턴스에서 공유하는 운영 환경에는 관계형 데이터베이스가 더 적합합니다.

## 테스트

```bash
pip install -r requirements-dev.txt
pytest
```

## 구조

```text
app.py                     # Streamlit 화면과 사용자 액션
book_rental/service.py     # 권한 및 대여 비즈니스 규칙
book_rental/store.py       # CSV 스키마, 잠금, 원자적 파일 저장
book_rental/errors.py      # 사용자 표시용 도메인 예외
data/                      # 초기 CSV 데이터와 업로드 디렉터리
tests/test_service.py      # 핵심 대여 흐름 테스트
```

상세 설계는 [`docs/architecture.md`](docs/architecture.md)를 참고하세요.
