# Neo V1 — Hooks 설치 가이드

Neo V1의 실행 강제력은 두 레이어로 구성됩니다.

```
레이어 1: Hermes Hooks (세션 레벨)
  - 도구 호출 차단 (pre_tool_call)
  - 테스트 자동 실행 (post_tool_call)
  - meta-코드 일관성 검증 (pre_llm_call)
  - 절대 금지선 매 턴 주입 (pre_llm_call)
  - 세션 시작 자동화 (on_session_start)

레이어 2: Git Hooks (커밋 레벨)
  - pytest·린트·보안 스캔 강제
  - 민감 키 하드코딩 차단
  - main/develop 직접 커밋 차단
```

---

## Hermes Hooks 설치

### Step 1. 훅 스크립트 복사

```bash
# ~/.hermes/neo-hooks/ 디렉토리 생성
mkdir -p ~/.hermes/neo-hooks/

# 훅 파일 복사
cp hooks/forbidden-check.py         ~/.hermes/neo-hooks/
cp hooks/auto-test.py               ~/.hermes/neo-hooks/
cp hooks/meta_consistency_check.py  ~/.hermes/neo-hooks/
cp hooks/context-inject.py          ~/.hermes/neo-hooks/
cp hooks/session-start.py           ~/.hermes/neo-hooks/
chmod +x ~/.hermes/neo-hooks/*.py
```

### Step 2. config.yaml에 hooks 블록 추가 (덮어쓰기 금지)

```bash
# 반드시 수동 편집 — 기존 설정 보존
hermes config edit
```

→ 열린 편집기에서 `hooks:` 섹션이 없으면 추가, 있으면 기존 목록 뒤에 추가:

```yaml
hooks:
  - event: pre_tool_call
    command: ~/.hermes/neo-hooks/forbidden-check.py
    matcher: write_file|patch|terminal
    timeout: 5
  - event: post_tool_call
    command: ~/.hermes/neo-hooks/auto-test.py
    matcher: write_file|patch
    timeout: 60
  - event: pre_llm_call
    command: ~/.hermes/neo-hooks/meta_consistency_check.py
    timeout: 5
  - event: pre_llm_call
    command: ~/.hermes/neo-hooks/context-inject.py
    timeout: 5
  - event: on_session_start
    command: ~/.hermes/neo-hooks/session-start.py
    timeout: 10
```

### Step 3. 동작 확인

```bash
hermes --version   # Hermes 버전 확인
# 세션 시작 후 훅이 자동 실행되는지 확인
```

---

## Git Hooks 설치

```bash
# 프로젝트 루트에서 실행
cp hooks/git/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# 동작 확인
git add . && git commit -m "test" --dry-run
```

---

## 훅별 커버 범위

| 훅 | 이벤트 | 커버 범위 | 강제 수준 |
|----|--------|-----------|-----------|
| forbidden-check | pre_tool_call | 절대 금지선 위반 차단 | 결정론적 (100%) |
| auto-test | post_tool_call | TDD 준수 | 결정론적 (100%) |
| meta_consistency_check | pre_llm_call | meta 인덱스-코드 불일치 경고 | 매 턴 (100%) |
| context-inject | pre_llm_call | 컨텍스트 압축 후 복원 | 매 턴 (100%) |
| session-start | on_session_start | neo-start 자동 실행 | 자동 (100%) |
| pre-commit (Git) | 커밋 시점 | 코드 품질·보안·브랜치 | 결정론적 (100%) |

---

## 훅 커스터마이징

### 프로젝트 고유 금지 패턴 추가

forbidden-check/handler.py를 수정하지 않아도 됩니다.
.hermes.md에 Omission Constraints를 작성하면 자동으로 로드됩니다.

### 테스트 명령어 변경

auto-test/handler.py의 TEST_RUNNER_CONFIG를 수정합니다.

```python
TEST_RUNNER_CONFIG = {
    "python": {
        "command": ["python", "-m", "pytest", "--tb=short", "-q"],
        # 필요 시 변경
    },
}
```

### 컨텍스트 주입 비활성화

세션이 짧아서 압축 문제가 없다면 context-inject를 비활성화합니다.
config.yaml에서 pre_llm_call 섹션을 주석 처리합니다.

---

## 강제력 수준 정리

```
Hermes Hooks + Git Hooks 조합:
  코드 품질 (pytest·린트·포맷):  100% (Git Hooks 차단)
  절대 금지선 위반:              ~95% (Hermes pre_tool_call)
  컨텍스트 압축 후 복원:         100% (매 턴 주입)
  TDD 준수:                    ~90% (파일 저장 후 자동 테스트)
  meta 인덱스 일관성:            100% (매 턴 pre_llm_call — 불일치 경고)
  설계 문서 갱신 여부:           ~70% (스킬 흐름에 의존)

전체 실행 강제력: ~95%
(Kiro Hooks 100% 대비 5% 차이 — 설계 문서 영역)
```
