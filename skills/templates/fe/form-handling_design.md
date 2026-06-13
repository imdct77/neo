# 폼 처리 — 설계 뷰 (AC용)

> **로드 시점**: Phase 0~2 (AC가 아키텍처 설계 시)
> **구현 코드**: `form-handling_impl.md` 참조

---

## 폼 상태 소유 경계

```
폼 입력 상태        → react-hook-form (useForm)
유효성 검사 스키마  → zod
서버 제출 상태      → TanStack Query useMutation (CSR)
                   또는 Server Action (SSR 폼)
UI 컴포넌트         → shadcn/ui Form, Input, Select 등
```

**이 네 가지가 분리되어야 한다.**
하나의 컴포넌트에서 useState로 입력을 관리하면서 fetch도 직접 호출하는 패턴을 사용하지 않는다.

---

## 서버 액션 vs CSR 뮤테이션 선택 기준

| 상황 | 방식 | 이유 |
|------|------|------|
| 폼 제출 후 페이지 이동 | Server Action | 서버에서 redirect 처리 |
| 폼 제출 후 UI 부분 갱신 | CSR + useMutation | 클라이언트 상태 갱신 필요 |
| 인증 폼 (로그인) | CSR + useMutation | 토큰 저장이 클라이언트에서 필요 |
| 파일 업로드 | Server Action | 멀티파트 처리 |

---

## 유효성 검사 경계

```
클라이언트 검사 (zod + react-hook-form):
  → 즉각적인 피드백. 서버 부하 감소
  → 필수값, 형식, 길이 등 단순 규칙

서버 검사 (BE Pydantic):
  → 신뢰할 수 있는 최종 검증
  → 중복 검사, DB 의존 규칙, 보안 검사

클라이언트 검사는 사용자 경험 개선용이다.
서버 검사를 클라이언트로 대체하지 않는다.
```

---

## Task 분리 기준

| 작업 | 분류 | 선행 조건 |
|------|------|---------|
| zod 스키마 정의 | 도메인 Task | BE API 계약 확정 후 |
| 폼 컴포넌트 | 도메인 Task | zod 스키마 완료 후 |
| 서버 액션 또는 뮤테이션 훅 | 도메인 Task | API 클라이언트 완료 후 |

---

## 주의: 설계에서 자주 발생하는 실수

- 클라이언트 zod 스키마와 BE Pydantic 스키마의 필드명 불일치 → camelCase/snake_case 변환 레이어 필요
- 폼 에러를 `alert()`으로 표시 → shadcn FormMessage 컴포넌트 사용
- 서버 에러를 클라이언트 폼 에러로 매핑하지 않음 → 제출 실패 시 어느 필드가 문제인지 사용자가 모름
