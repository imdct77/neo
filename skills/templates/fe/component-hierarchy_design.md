# 컴포넌트 계층 — 설계 뷰 (AC용)

> **로드 시점**: Phase 0~2 (AC가 아키텍처 설계 시)
> **구현 코드**: `component-hierarchy_impl.md` 참조

---

## 컴포넌트 트리 구조

```
app/ (Next.js App Router)
    layout.tsx              ← 전역 레이아웃 (Server Component)
    page.tsx                ← 페이지 진입점 (Server Component)
        └── {Feature}Page   ← 페이지 단위 컨테이너 (Server Component)
                ├── {Feature}Header     ← UI 전용 (Server/Client)
                ├── {Feature}List       ← 데이터 소유 (Server Component)
                │       └── {Feature}Card  ← 표현 전담 (Server Component)
                └── {Feature}Form       ← 상호작용 (Client Component)
```

---

## Server Component vs Client Component 분리 기준

| 판단 기준 | Server Component | Client Component |
|---------|-----------------|-----------------|
| 데이터 패칭 | ✅ fetch, DB 직접 | ❌ |
| 브라우저 API | ❌ | ✅ window, localStorage |
| 이벤트 핸들러 | ❌ | ✅ onClick, onChange |
| useState, useEffect | ❌ | ✅ |
| 민감 환경변수 | ✅ 안전 | ❌ 노출 위험 |

**원칙: Client Component는 최대한 트리의 말단(Leaf)에 둔다.**
상위 컴포넌트가 Client가 되면 하위 전체가 Client 번들에 포함된다.

---

## 상태 소유 경계

```
서버 상태 (DB/API 데이터)
    → TanStack Query가 관리
    → Server Component에서는 직접 fetch

클라이언트 전역 상태 (로그인 사용자, 테마, 모달 등)
    → Zustand store
    → Client Component에서만 접근

로컬 UI 상태 (폼 입력, 드롭다운 열림 등)
    → useState
    → 해당 컴포넌트 안에서만 관리
```

상태가 "이 컴포넌트에서만 쓰이는가?"라면 → useState
상태가 "여러 컴포넌트에서 공유되는가?"라면 → 서버 상태면 TanStack Query, 클라이언트면 Zustand

---

## 폴더 구조 기준

```
src/fe/
  app/                    ← Next.js App Router (라우팅)
    (auth)/               ← 라우트 그룹
      login/page.tsx
    (dashboard)/
      page.tsx
      layout.tsx
  components/
    ui/                   ← shadcn/ui 원본 (수정 금지)
    common/               ← 도메인 무관 공통 컴포넌트
    {domain}/             ← 도메인별 컴포넌트
  hooks/                  ← 커스텀 훅
  stores/                 ← Zustand 스토어
  lib/                    ← 유틸리티, API 클라이언트
  types/                  ← 타입 정의
```

---

## Task 분리 기준

| 작업 | 분류 | 선행 조건 |
|------|------|---------|
| 레이아웃 컴포넌트 | 공통 Task | 없음 |
| 공통 UI 컴포넌트 | 공통 Task | 없음 |
| 도메인 페이지 | 도메인 Task | 공통 완료 후 |
| 도메인 폼 컴포넌트 | 도메인 Task | 페이지 구조 확정 후 |

---

## 주의: 설계에서 자주 발생하는 실수

- 페이지 컴포넌트에 모든 로직 집중 → 500줄 페이지 컴포넌트
- Client Component를 루트 레이아웃에 배치 → 전체 앱이 Client 번들
- 상태를 props로 5단계 이상 전달 → Context 또는 전역 상태 검토
- shadcn/ui 컴포넌트를 `components/ui/`에서 직접 수정 → 업데이트 시 덮어씌워짐
