# templates/ — 구현 패턴 템플릿

> **목적**: 반복되는 설계·구현 패턴을 표준화. 에이전트가 작업 전 이 파일을 확인하고 해당 템플릿을 로드한다.

## 로딩 규칙

1. **작업 시작 시** 이 README.md를 확인하여 적용 가능한 패턴이 있는지 검색한다
2. **Phase 0~2 (설계)**: 해당 패턴의 `_design.md`를 로드 — 아키텍처 결정·Task 분리 기준 획득
3. **Phase 3 (구현)**: 해당 패턴의 `_impl.md`를 로드 — 실제 코드 패턴·컨벤션 획득
4. **shared/ 템플릿**: BE·FE 양쪽에서 필요 시 로드. BE/FE 프로필 §2-0에서 참조

> 템플릿이 없으면 자유 구현. 템플릿과 상황이 다르면 "이 템플릿을 따르지 않는 이유"를 Task Brief에 명시.

---

## 패턴 인덱스

### BE (백엔드 — Python / FastAPI / SQLAlchemy)

| 패턴 | Design | Impl | 적용 상황 |
|------|:---:|:---:|------|
| **Repository 패턴** | [`repository-pattern_design.md`](be/repository-pattern_design.md) | [`repository-pattern_impl.md`](be/repository-pattern_impl.md) | DB 접근 계층 분리. 데이터 영속성 로직이 Service에 섞일 때 |
| **트랜잭션** | [`transaction_design.md`](be/transaction_design.md) | [`transaction_impl.md`](be/transaction_impl.md) | 여러 DB 작업을 원자적으로 묶어야 할 때 |
| **에러 처리** | [`error-handling_design.md`](be/error-handling_design.md) | [`error-handling_impl.md`](be/error-handling_impl.md) | 예외 계층·HTTP 상태코드 매핑 설계 |
| **DI (의존성 주입)** | [`dependency-injection_design.md`](be/dependency-injection_design.md) | [`dependency-injection_impl.md`](be/dependency-injection_impl.md) | FastAPI Depends 체인. Service·Repository 연결 |
| **API 계약** | [`api-contract_design.md`](be/api-contract_design.md) | [`api-contract_impl.md`](be/api-contract_impl.md) | 엔드포인트 설계·버전 관리·요청/응답 스키마 |

### FE (프론트엔드 — Next.js / React / Tailwind)

| 패턴 | Design | Impl | 적용 상황 |
|------|:---:|:---:|------|
| **컴포넌트 계층** | [`component-hierarchy_design.md`](fe/component-hierarchy_design.md) | [`component-hierarchy_impl.md`](fe/component-hierarchy_impl.md) | 페이지 구조·Server/Client 분리·폴더 구조 |
| **상태 관리** | [`state-management_design.md`](fe/state-management_design.md) | [`state-management_impl.md`](fe/state-management_impl.md) | 서버/전역/로컬 상태 분류·TanStack Query·Zustand |
| **데이터 페칭** | [`data-fetching_design.md`](fe/data-fetching_design.md) | [`data-fetching_impl.md`](fe/data-fetching_impl.md) | API 통신·캐싱·에러/로딩 상태·낙관적 업데이트 |
| **폼 처리** | [`form-handling_design.md`](fe/form-handling_design.md) | [`form-handling_impl.md`](fe/form-handling_impl.md) | react-hook-form·유효성 검사·서버 에러 |
| **에러 바운더리** | [`error-boundary_design.md`](fe/error-boundary_design.md) | [`error-boundary_impl.md`](fe/error-boundary_impl.md) | 컴포넌트 트리 에러 격리·Fallback UI |
| **스타일링** | — | [`styling.md`](fe/styling.md) | Tailwind·shadcn/ui·반응형·다크 모드·디자인 토큰 |

### Shared (공통 — BE·FE 양쪽)

| 패턴 | Design | Impl | 적용 상황 |
|------|:---:|:---:|------|
| **인증/인가** | [`auth_design.md`](shared/auth_design.md) | [`auth_impl.md`](shared/auth_impl.md) | JWT·로그인/토큰 갱신·RBAC·FE 인증 흐름 |
| **로깅** | [`logging_design.md`](shared/logging_design.md) | [`logging_impl.md`](shared/logging_impl.md) | 구조화 로깅·로그 레벨·민감 정보 필터링 |

---

## 템플릿 구조 규약

모든 템플릿은 아래 규칙을 따른다:

```
Design 템플릿 (_design.md):
- "AC용" — 아키텍처 단계에서 로드
- 레이어 구조 / 판단 기준 / 경계 정의
- Task 분리 기준 (어떤 Task로 쪼갤지)
- 자주 발생하는 실수

Impl 템플릿 (_impl.md):
- "BE용" / "FE용" — 구현 단계에서 로드
- 스택 명시 (Python/FastAPI/SQLAlchemy 등)
- 실제 실행 가능한 코드 예시
- 구현 규칙·주의사항
```

---

## 템플릿 추가 가이드

새 패턴 템플릿 추가 시:

1. `{pattern}_design.md` + `{pattern}_impl.md` 쌍으로 작성
2. 이 README.md의 해당 카테고리(BE/FE/shared) 표에 행 추가
3. `_design.md` 첫 줄에 `> **구현 코드**: \`{pattern}_impl.md\` 참조` 링크
4. `_impl.md` 첫 줄에 `> **설계 구조**: \`{pattern}_design.md\` 참조` 링크
