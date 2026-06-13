# 에러 바운더리 — 설계 뷰 (AC용)

> **로드 시점**: Phase 0~2 (AC가 아키텍처 설계 시)
> **구현 코드**: `error-boundary_impl.md` 참조

---

## 에러 전파 범위

```
app/
    error.tsx              ← 전역 에러 경계 (최후 방어선)
    (dashboard)/
        error.tsx          ← 대시보드 섹션 에러 경계
        orders/
            error.tsx      ← 주문 페이지 에러 경계
            page.tsx
                └── <ErrorBoundary>  ← 컴포넌트 레벨 에러 경계
                        └── <OrderList />
```

에러 경계는 **영향 범위를 최소화**하는 것이 목표다.
전체 페이지가 에러로 내려가지 않도록 컴포넌트 레벨에서 먼저 잡는다.

---

## 폴백 UI 배치 기준

| 에러 범위 | 폴백 UI | 위치 |
|---------|---------|------|
| 전체 앱 | "서비스 오류" 전체 페이지 | `app/error.tsx` |
| 페이지 단위 | "이 페이지를 불러올 수 없음" + 재시도 버튼 | `app/{route}/error.tsx` |
| 섹션 단위 | "이 섹션을 불러올 수 없음" + 재시도 | 컴포넌트 레벨 ErrorBoundary |
| 비동기 데이터 | Skeleton → 에러 메시지 | TanStack Query isError 처리 |

---

## Not Found 처리 설계

```
존재하지 않는 리소스 접근:
  → notFound() 호출 (Server Component)
  → app/not-found.tsx 렌더링

존재하지 않는 라우트:
  → Next.js 기본 404 처리
  → app/not-found.tsx 재사용
```

---

## 주의: 설계에서 자주 발생하는 실수

- 전역 `app/error.tsx` 하나만 두기 → 작은 섹션 에러가 전체 페이지를 내림
- 에러 바운더리 없이 async 컴포넌트 → 에러가 상위로 전파되어 예측 불가한 범위가 다운됨
- loading.tsx와 error.tsx 누락 → Next.js Suspense 기반 스트리밍이 올바르게 동작하지 않음
