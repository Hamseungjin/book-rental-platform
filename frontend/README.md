# BookBridge Frontend

Vite + React + TypeScript + React Router + TanStack Query + Axios + Tailwind CSS로 구현한 책 대여 플랫폼 UI입니다.

## 실행

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

기본 API 주소는 `http://localhost:8080`입니다. `VITE_API_BASE_URL=/api`로 설정하면 `vite.config.ts`의 개발 프록시를 사용합니다. 운영 빌드는 `npm run build`로 생성합니다.

## 임시 인증

화면 상단에서 사용자 ID를 입력합니다. 일반/등록자/반납 API에는 `X-User-Id`, 관리자 API에는 `X-Admin-Id`가 자동으로 전송됩니다. 역할 기반 메뉴 제어는 UX 편의 기능일 뿐이며 실제 보안은 백엔드에서 검증해야 합니다.

## 백엔드 미지원 필드와 API

- 책의 `publisher`, `condition`, `coverImageUrl`은 현재 `BookDtos.UpsertRequest`에 없어 폼에 미지원 안내만 표시하고 전송하지 않습니다.
- 백엔드 필드 `defaultLoanDays`를 화면에서 “기본 대여 기간”으로 사용합니다.
- BORROWER 본인의 대출 이력 조회 API가 없어 요청 목록 화면에 TODO로 표시합니다.
