# 상태 관리 — 설계 뷰 (AC용)

> **로드 시점**: Phase 0~2 (AC가 아키텍처 설계 시)
> **구현 코드**: `state-management_impl.md` 참조

---

## 상태 분류 기준

```
서버 상태 (Server State)
    정의: DB/API에서 오는 데이터. 비동기, 캐시 필요, 여러 컴포넌트 공유
    담당: TanStack Query (Client) / 직접 fetch (Server Component)
    예: 주문 목록, 사용자 정보, 상품 데이터

클라이언트 전역 상태 (Global Client State)
    정의: 브라우저 세션 동안 유지. 서버와 무관
    담당: Zustand
    예: 현재 로그인 사용자, 사이드바 열림 여부, 선택된 테마

로컬 UI 상태 (Local UI State)
    정의: 특정 컴포넌트 안에서만 사용
    담당: useState / useReducer
    예: 모달 열림 여부, 입력 중인 텍스트, 탭 선택
```

**판단 흐름:**
```
이 상태가 API/DB 데이터인가?
  YES → 서버 상태 → TanStack Query
  NO  → 여러 컴포넌트에서 공유하는가?
          YES → 전역 클라이언트 상태 → Zustand
          NO  → 로컬 UI 상태 → useState
```

---

## 서버 상태 설계 기준

| 항목 | 기준 |
|------|------|
| 캐시 키 구조 | `[도메인, 리소스ID, 파라미터]` 배열 형태 |
| staleTime | 자주 바뀌지 않는 데이터: 5분. 실시간 데이터: 0 |
| 뮤테이션 후 갱신 | 성공 시 관련 쿼리 invalidate |
| 에러 처리 | 쿼리 레벨 onError + 전역 QueryClient onError |
| 로딩 상태 | Suspense 경계 + Skeleton UI |

---

## 전역 상태 설계 기준

Zustand 스토어는 도메인별로 분리한다:
```
stores/
  useAuthStore.ts      ← 인증 상태
  useUIStore.ts        ← UI 전역 상태 (사이드바, 모달)
  use{Domain}Store.ts  ← 도메인별 선택/필터 상태
```

**스토어에 넣지 않는 것:**
- 서버에서 오는 데이터 (TanStack Query 역할)
- 단일 컴포넌트만 쓰는 상태 (useState 역할)
- 폼 입력 상태 (react-hook-form 역할)

---

## Task 분리 기준

| 작업 | 담당 | 선행 조건 |
|------|------|---------|
| QueryClient 설정 | 공통 Task | 없음 |
| 도메인 쿼리 훅 작성 | 도메인 Task | API 계약 확정 후 |
| Zustand 스토어 정의 | 공통 Task | 없음 |
| 컴포넌트 상태 연결 | 도메인 Task | 쿼리 훅 완료 후 |

---

## 주의: 설계에서 자주 발생하는 실수

- 서버 데이터를 Zustand에 저장 → TanStack Query 캐시와 이중 관리, 불일치 발생
- 전역 스토어가 비대해짐 → 도메인별로 분리하고 스토어 하나당 한 가지 관심사
- 모든 비동기 상태를 useState+useEffect로 관리 → 로딩/에러/캐시 모두 수동 관리 필요
