# 데이터 패칭 — 설계 뷰 (AC용)

> **로드 시점**: Phase 0~2 (AC가 아키텍처 설계 시)
> **구현 코드**: `data-fetching_impl.md` 참조

---

## SSR / SSG / CSR 선택 기준

| 데이터 특성 | 렌더링 방식 | Next.js 구현 |
|-----------|-----------|------------|
| SEO 필요 + 자주 바뀜 | SSR | Server Component + fetch (no-store) |
| SEO 필요 + 거의 안 바뀜 | SSG | Server Component + fetch (force-cache) |
| SEO 불필요 + 사용자별 데이터 | CSR | Client Component + TanStack Query |
| SEO 불필요 + 실시간 업데이트 | CSR + Polling/WS | Client Component + TanStack Query |

**원칙: SEO가 필요 없고 사용자 인터랙션이 필요한 데이터는 CSR로 처리한다.**
Server Component에서 무리하게 데이터를 패칭하면 스트리밍 이점이 사라진다.

---

## 캐시 전략 설계 기준

```
자주 바뀌지 않는 공통 데이터 (카테고리, 설정 등)
  → revalidate: 3600 (1시간)

사용자별 데이터 (프로필, 주문 등)
  → no-store (캐시 없음)

정적 콘텐츠 (약관, FAQ 등)
  → force-cache

API Route Handler
  → 인증 필요한 경우 no-store
  → 공개 데이터는 revalidate 설정
```

---

## API 클라이언트 설계 기준

Server Component용과 Client Component용을 분리한다:

```
lib/api/
  server.ts    ← Server Component 전용 (서버 환경 변수 사용 가능)
  client.ts    ← Client Component 전용 (브라우저에서 실행)
  {domain}.ts  ← 도메인별 API 함수
```

---

## Task 분리 기준

| 작업 | 분류 | 선행 조건 |
|------|------|---------|
| API 클라이언트 기반 설정 | 공통 Task | BE API 계약 확정 후 |
| Server Component 패칭 함수 | 도메인 Task | API 클라이언트 완료 후 |
| TanStack Query 훅 | 도메인 Task | API 클라이언트 완료 후 |

---

## 주의: 설계에서 자주 발생하는 실수

- Server Component에서 패칭한 데이터를 TanStack Query로 중복 패칭
- Client Component에서 `NEXT_PUBLIC_` 없는 환경변수 사용 → 런타임 오류
- Route Handler를 Server Component 대신 항상 거치는 설계 → 불필요한 네트워크 왕복
