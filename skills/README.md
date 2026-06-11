# docs/skills/ — Neo V1 참조 문서 모음

> **이 디렉토리의 파일들은 Hermes 내장 스킬이 아닙니다.**
> Hermes의 `~/.hermes/skills/`에 등록된 스킬과 무관합니다.
>
> NEO가 특정 조건에서 해당 파일을 직접 읽어(파일 읽기) 내용을 따르는
> **Neo V1 자체 업무 절차 문서**입니다.
> AGENTS.md의 트리거 조건에 따라 자동으로 참조됩니다.

---

## 왜 Hermes 스킬로 등록하지 않는가

```
문제 1. 프론트매터 강제
  모든 파일에 YAML 메타데이터 필수 → 13개 파일 모두 수정 필요

문제 2. 스킬 간 의존성 단절
  Neo 스킬은 파이프라인 (phase0 → gate → review → finish)
  Hermes 스킬은 각자 독립적으로 설계되어야 함 → 구조 충돌

문제 3. 프로필 스코프 문제
  Neo 스킬은 프로젝트 디렉토리 안에 있어야 함
  Hermes 스킬은 ~/.hermes/skills/ 전역 또는 프로필별

문제 4. Curator 간섭
  사용량 추적·자동 아카이빙 대상이 되면
  워크플로우 파이프가 끊길 위험
```

---

## 스킬 목록 및 요약

| 파일 | 트리거 조건 | 역할 요약 |
|------|------------|----------|
| `neo-start.md` | 세션 시작 시 | 파일 로드·mem0 검색·칸반 상태 확인·상태 보고. 첫 세션이면 design-init 실행. |
| `phase0.md` | 새 기능·API·컴포넌트 작업 전 | mem0 적합성·영향도 탐색 → AC 설계 검토 → BE·FE 병렬 검토 → 설계 문서 저장. |
| `gate.md` | Task Brief 전달 직전 | Q1~Q7 체크리스트. 해당 시 ADR 작성·승인 후 진행. |
| `review.md` | 구현 완료 후 | Critical·Important·Minor 분류 코드 리뷰. 구현자가 자신의 코드 리뷰 금지. |
| `debug.md` | 버그·오류 발생 시 | 재현→가설→검증→수정 4단계. 증상 즉시 수정 금지. |
| `finish.md` | 모든 태스크 완료 후 | MERGE·PR·KEEP·DISCARD 선택. 병합 조건 확인. |
| `ctx.md` | /ctx·/ctx add·/ctx drop | 도메인 문서 로딩·제거·조회. docs/requirements/ 동적 탐색. |
| `design-init.md` | 새 프로젝트 첫 세션 | 아이디어 구체화 대화 진입점. 조건 충족 시 design-* 스킬 순차 연결. |
| `design-arch.md` | architecture.md 작성 조건 충족 시 | 전체 아키텍처 문서 작성 기준. 운영·보안·트래픽 포함. |
| `design-db.md` | database.md 작성 조건 충족 시 | DB 설계 문서 작성 기준·갱신 정책. AC+BE 협업. |
| `design-api.md` | api/ 작성 조건 충족 시 | API 협업 루프. BLOCKER 기반 종료. 싱글 에이전트 순차. |
| `design-screens.md` | screens/ 작성 조건 충족 시 | 화면 설계 문서 작성. STATE 정의 → tests 자동 도출. |
| `kanban.md` | Phase 전환·태스크 시작·완료·BLOCKED | Hermes 칸반 연동 규칙. 진척도 가시화. |
| `badcase-review.md` | finish.md MERGE/PR 또는 DISCARD 선택 후 | 도메인 단위 BADCASE 집계 → 패턴 추출 → 규칙 적용. SCOPE 즉시 승격 포함. |
| `badcase-distill.md` | MVP 완성 후 | 프로젝트 전체 BADCASE 증류 → 효과 검증 → 장기 반영. SCOPE 재평가 포함. |

---

## 트리거 흐름

```
세션 시작
  └→ neo-start

새 프로젝트
  └→ neo-start → design-init
                  └→ design-arch
                  └→ design-db
                  └→ design-api
                  └→ design-screens

새 기능 개발
  └→ phase0 → (Task Brief 전) gate → (구현 후) review → finish

버그 발생
  └→ debug

/ctx 명령
  └→ ctx

Phase 전환·완료·BLOCKED
  └→ kanban

도메인 완료 (finish.md MERGE/PR 또는 DISCARD 선택)
  └→ badcase-review (도메인 단위 BADCASE 학습)

프로젝트 완료 (MVP)
  └→ badcase-distill (프로젝트 전체 BADCASE 증류)
```

---

## /ctx 주의사항

`/ctx`는 **Hermes 내장 슬래시 명령이 아닙니다.**
Neo V1 자체 커맨드입니다.
Hermes가 인식하지 못하면 "컨텍스트 문서 목록 보여줘" 등 자연어로 대신 사용하세요.
