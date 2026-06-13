# Neo V1 — 범용 바이브코딩 하네스

Neo V1은 Hermes + mem0 환경에서 동작하는 범용 바이브코딩 하네스입니다.
어떤 소프트웨어 프로젝트에도 적용할 수 있습니다.

설치 및 사용법은 `SETUP.md`를 참조하세요.

---

## 루트 파일

| 파일 | 역할 |
|------|------|
| `SETUP.md` | `harness/` | 새 프로젝트 설치 가이드. 플레이스홀더 작성법·Hooks 설치 안내. |
| `SOUL.md` | `harness/` → `~/.hermes/SOUL.md`에 설치. NEO의 전역 정체성. 모든 세션에 적용. |
| `.hermes.md` | `harness/` | Omission Constraints 템플릿 + Project Identity에 배치. Omission Constraints 템플릿. Hermes 최우선 로드. |
| `AGENTS.md` | `harness/` | 프로젝트 헌법. 역할·스택·절대 금지선·게이트·브랜치 전략. |
| `setup.py` | `harness/` | 설치 자동화 스크립트. 플레이스홀더 자동 치환·Hooks 설치. |
| `project.json` | `harness/` | 프로젝트 메타데이터 SSoT (project_id, git URLs). | Phase -1~4 전체 흐름. 모든 프로젝트 공통. |

---

## 프로필 파일 (역할별 정체성)

| 파일 | 역할 코드 | 역할 |
|------|----------|------|
| `harness/personas/orchestrator.md` | NEO | Orchestrator. 사람과 소통·전체 조율. 기본 프로필. |
| `harness/personas/architect.md` | AC | 아키텍처 검토·게이트 담당. |
| `harness/personas/backend.md` | BE | 백엔드 구현 전담. |
| `harness/personas/frontend.md` | FE | 프론트엔드 구현 전담. |
| `harness/personas/qa.md` | QA | 감리 전담. **반드시 다른 LLM 모델로 동작.** |

---

## 디렉토리 구조

### harness/ (imdct77/neo) — 도구·규칙·상태

| 디렉토리 | 역할 |
|----------|------|
| `harness/hooks/` | Hermes + Git 훅. 실행 강제력. |
| `harness/personas/` | 역할별 프로필 파일. |
| `harness/skills/` | Neo 스킬 (트리거 조건 시 자동 로드). 상세: `harness/skills/README.md` |
| `harness/works/` | 업무 파이프라인 템플릿. |
| `harness/state/` | Neo 구조적 상태. `.neo_state.json`, 메타 인덱스. |
| `harness/state/meta/` | 코드 메타 인덱스 (3계층). L1/L2/L3 자동 동기화. |

### project/ (imdct77/{project_id}) — 산출물·소스코드

| 디렉토리 | 생성 시점 | 역할 |
|----------|----------|------|
| `project/src/be/` | 설치 시 | 백엔드 소스코드 (하위 구조는 BE가 결정) |
| `project/src/fe/` | 설치 시 | 프론트엔드 소스코드 (하위 구조는 FE가 결정) |
| `project/docs/design/` | Phase -1 | 전체 설계 문서. architecture·database·api·screens. |
| `project/docs/requirements/` | Phase 0 | 도메인별 요구사항 (EARS 문법). |
| `project/docs/tasks/` | Phase 1 | 도메인별 구현 태스크. BE·FE 분리. |
| `project/docs/tests/` | Phase 1 | 도메인별 테스트 정의. |
| `project/docs/briefs/` | Phase 3 | Task Brief. 태스크별 작업 지시서. |
| `project/docs/specs/` | Phase 0 | AC 기능별 설계 문서. |
| `project/docs/qa/` | QA 감리 시 | QA 감리 보고서. |
| `project/docs/issues/` | 이슈 발생 시 | 이슈별 대화 이력. |
| `project/docs/plans/` | Phase 3 | Plan 문서. |

> harness와 project는 별도 Git 레포. `project/.git/hooks/pre-commit` 프록시가
> harness의 `meta_consistency_check.py --sync`를 호출하여 3계층 메타 인덱스 자동 동기화.

---

## 템플릿 파일

프로젝트마다 복사해서 채워 쓰는 파일들입니다.

| 파일 | 용도 |
|------|------|
| `harness/works/task_brief_templ.md` | Task Brief 작성 기준. |
| `harness/works/tasks_templ.md` | BE·FE tasks 작성 기준. |
| `harness/works/tests_templ.md` | 테스트 정의 작성 기준. |

---

## Hooks

| 디렉토리 | 역할 |
|----------|------|
| `harness/hooks/` | Hermes Hooks. 실행 강제력 ~95%. 설치: `harness/hooks/HOOKS_SETUP.md`. 실행 강제력 ~95%. 설치: `hooks/HOOKS_SETUP.md` 참조. |
| `harness/hooks/git/` | Git pre-commit. 코드 품질·보안.. 코드 품질·보안·브랜치 보호. |

---

## 빠른 시작

```bash
python3 setup.py   # 플레이스홀더 자동 치환 + Hooks 설치
# → .hermes.md Omission Constraints 작성
# → Hermes에서 "NEO, 시작해줘"
```

## Version History
- **V2.02** — 소스 디렉토리 표준화 (src/be/, src/fe/)
