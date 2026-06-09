# Neo V1 — 범용 바이브코딩 하네스

Neo V1은 Hermes + mem0 환경에서 동작하는 범용 바이브코딩 하네스입니다.
어떤 소프트웨어 프로젝트에도 적용할 수 있습니다.

설치 및 사용법은 `SETUP.md`를 참조하세요.

---

## 루트 파일

| 파일 | 역할 |
|------|------|
| `SETUP.md` | 새 프로젝트 설치 가이드. 플레이스홀더 작성법·Hooks 설치 안내. |
| `SOUL.md` | `~/.hermes/SOUL.md`에 설치. NEO의 전역 정체성. 모든 세션에 적용. |
| `.hermes.md` | 프로젝트 루트에 배치. Omission Constraints 템플릿. Hermes 최우선 로드. |
| `AGENTS.md` | 프로젝트 헌법. 역할·스택·절대 금지선·게이트·브랜치 전략. |
| `setup.py` | 설치 자동화 스크립트. 플레이스홀더 자동 치환·Hooks 설치. |
| `workflow.md` | NEO 업무 절차서. Phase -1~4 전체 흐름. 모든 프로젝트 공통. |

---

## 프로필 파일 (역할별 정체성)

| 파일 | 역할 코드 | 역할 |
|------|----------|------|
| `orchestrator_profile.md` | NEO | Orchestrator. 사람과 소통·전체 조율. 기본 프로필. |
| `architect_profile.md` | AC | 아키텍처 검토·게이트 담당. |
| `backend_profile.md` | BE | 백엔드 구현 전담. |
| `frontend_profile.md` | FE | 프론트엔드 구현 전담. |
| `qa_profile.md` | QA | 감리 전담. **반드시 다른 LLM 모델로 동작.** |

---

## docs/ 하위 디렉토리 구조

프로젝트 진행 중 아래 디렉토리들이 생성됩니다.

| 디렉토리 | 생성 시점 | 역할 |
|----------|----------|------|
| `docs/skills/` | 설치 시 | Neo V1 참조 문서 모음. 상세는 `docs/skills/README.md` 참조. |
| `docs/design/` | Phase -1 | 전체 설계 문서. architecture·database·api·screens. |
| `docs/requirements/` | Phase 0 | 도메인별 요구사항 (EARS 문법). |
| `docs/tasks/` | Phase 1 | 도메인별 구현 태스크. BE·FE 분리. |
| `docs/tests/` | Phase 1 | 도메인별 테스트 정의. |
| `docs/briefs/` | Phase 3 | Task Brief. 태스크별 작업 지시서. |
| `docs/specs/` | Phase 0 | AC 기능별 설계 문서. |
| `docs/qa/` | QA 감리 시 | QA 감리 보고서. |
| `docs/issues/` | 이슈 발생 시 | 이슈별 대화 이력. AC·BE·FE 의견 누적. |
| `docs/archive/issues/` | 이슈 종료 시 | 종료된 이슈 이력 보관. |
| `docs/design/decisions.md` | 이슈 종료 시 | 핵심 결정 사항 누적. |
| `docs/plans/` | Phase 3 | Plan 문서. |

---

## 템플릿 파일

프로젝트마다 복사해서 채워 쓰는 파일들입니다.

| 파일 | 용도 |
|------|------|
| `task_brief_templ.md` | Task Brief 작성 기준. |
| `tasks_templ.md` | BE·FE tasks 작성 기준. |
| `tests_templ.md` | 테스트 정의 작성 기준. |

---

## Hooks

| 디렉토리 | 역할 |
|----------|------|
| `hooks/` | Hermes Hooks 4개. 실행 강제력 ~95%. 설치: `hooks/HOOKS_SETUP.md` 참조. |
| `git-hooks/` | Git pre-commit Hook. 코드 품질·보안·브랜치 보호. |

---

## 빠른 시작

```bash
python3 setup.py   # 플레이스홀더 자동 치환 + Hooks 설치
# → .hermes.md Omission Constraints 작성
# → Hermes에서 "NEO, 시작해줘"
```

## Version History
- **V2.02** — 소스 디렉토리 표준화 (src/be/, src/fe/)
