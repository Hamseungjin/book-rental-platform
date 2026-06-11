# Frontend 구현 정리

## 기술 스택

- Vite, React 19, TypeScript
- React Router
- Axios API client
- TanStack Query 서버 상태 관리
- React Hook Form
- Tailwind CSS
- Lucide React 아이콘

## 주요 구조

```text
frontend/src
├── api              # Axios client, 백엔드 endpoint 함수
├── components       # Layout, 역할 가드, 공통 UI
├── features/auth    # 임시 사용자 ID 및 역할 조회 Context
├── pages            # 라우트 단위 페이지
├── types            # 백엔드 DTO 대응 TypeScript 타입
└── utils            # 날짜, 파일 크기, 상태 라벨
```

## 구현 페이지

- `/`, `/books`, `/books/:bookId`
- `/borrower/requests`
- `/lender/books`, `/lender/books/new`, `/lender/books/:bookId/edit`
- `/admin/dashboard`, `/admin/books/pending`, `/admin/borrow-requests`
- `/admin/loans`, `/admin/loans/overdue`

## 연결 API

| Method | API | 화면 |
|---|---|---|
| GET | `/api/users/{userId}` | 현재 사용자와 역할 조회 |
| GET | `/api/books` | 공개 도서 목록 |
| GET | `/api/books/{bookId}` | 도서 상세 |
| POST | `/api/borrow-requests` | 대여 요청 생성 |
| GET | `/api/borrow-requests/me` | 내 대여 요청 |
| GET/POST | `/api/lender/books` | 등록자 책 목록/등록 |
| PATCH | `/api/lender/books/{bookId}` | 등록자 책 수정 |
| GET | `/api/admin/dashboard` | 관리자 대시보드 |
| GET | `/api/admin/books/pending` | 승인 대기 책 |
| PATCH | `/api/admin/books/{bookId}/approve`, `/reject` | 책 승인/거절 |
| GET | `/api/admin/borrow-requests` | 전체 대여 요청 |
| PATCH | `/api/admin/borrow-requests/{id}/approve`, `/reject` | 요청 승인/거절 |
| GET | `/api/admin/loans`, `/api/admin/loans/overdue` | 현재 대출/연체 |
| PATCH | `/api/loans/{loanId}/return` | 반납 처리 |

## 인증 헤더

Axios interceptor는 선택한 사용자 ID를 `localStorage`에 저장하고 일반 API에 `X-User-Id`, `/api/admin` API에 추가로 `X-Admin-Id`를 전송한다. 프론트 역할 가드는 UX용이며 보안 경계가 아니다.

## 백엔드와의 차이 및 TODO

- 요구 화면의 `publisher`, `book condition`, `cover image URL`은 현재 `BookDtos.UpsertRequest`에 없으므로 disabled 필드와 안내 문구로 표시하며 API payload에는 넣지 않는다.
- 화면의 대여 기간은 백엔드 필드명인 `defaultLoanDays`에 맞췄다.
- BORROWER 대출 이력 조회 API가 없으므로 `/borrower/requests`에 TODO 안내를 표시한다.
- 브라우저에서 기본 `http://localhost:8080` API를 직접 호출할 수 있도록 백엔드에 최소 CORS 설정을 추가했다. `CORS_ALLOWED_ORIGINS`로 허용 origin을 쉼표 구분해 변경할 수 있다.
