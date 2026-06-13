---
name: state-manage
description: 상태 관리 명령어 레퍼런스. 상태 전환·CR 관리·git 이력 조회가 필요할 때 읽는다.
triggers:
  - 상태 전환 필요 시
  - CR 생성/승인/종료 시
  - 상태 파일 손상 시
  - "상태 바꿔줘"
  - "CR 만들어줘"
---

# ⚠️ 이 파일은 Hermes 내장 스킬이 아닙니다. NEO가 조건에 따라 직접 읽어 따르는 참조 문서입니다.

# state-manage — 상태 관리 명령어 레퍼런스

상태 전환 판단 기준과 에스컬레이션 규칙은 `harness/personas/orchestrator.md §4-2, §4-3`에 있다.
이 파일은 판단이 끝난 후 **어떻게 실행하는가**를 담는다.

---

## 1. 역할 분리 원칙

```
.neo_state.json  →  결정론적 차단 기준
                    "지금 무엇을 하면 안 되는가"
                    forbidden-check.py가 매 턴 자동 읽음
                    NEO가 상태 전환 시 직접 갱신

mem0             →  맥락 기반 복원과 학습
                    "어떻게 여기까지 왔는가, 무엇을 배웠는가"
                    세션 시작 시 보조 참조
                    Phase·Lifecycle 상태를 mem0에 기록하지 않는다

git 히스토리     →  시간적 상태 검증
                    "코드가 언제 어떻게 바뀌었는가"
                    meta staleness 감지에 활용
                    의미 있는 전환 시점에 git tag 생성

project/docs/    →  설계 근거
                    "무엇을 만들기로 했는가"
```

---

## 2. .neo_state.json 갱신 명령어

**.neo_state.json은 구조적 상태의 SSoT다.**
아래 시점마다 반드시 갱신한다.

### 도메인 추가
```bash
python3 hooks/state_manager.py add-domain \
  --domain {DOMAIN} \
  --deps {의존_도메인1} {의존_도메인2}   # 의존성 없으면 생략
```

### Lifecycle 전환
```bash
# 순방향 (NEO 자율 실행)
python3 hooks/state_manager.py lifecycle \
  --domain {DOMAIN} \
  --to {NEW_LIFECYCLE} \
  --reason "{전환 이유}"

# 역방향 (사람 승인 후에만 실행 — --approved 필수)
python3 hooks/state_manager.py lifecycle \
  --domain {DOMAIN} \
  --to {NEW_LIFECYCLE} \
  --reason "{전환 이유}" \
  --risk {low|medium|high} \
  --approved
```

유효한 Lifecycle 값: `REQUIREMENTS` `DESIGN` `IMPLEMENTATION` `VERIFICATION` `DEPLOYED`

### Phase 전환 (IMPLEMENTATION 내부)
```bash
python3 hooks/state_manager.py phase \
  --domain {DOMAIN} \
  --to {NEW_PHASE}
```

유효한 Phase 값: `-1` `0` `1` `2` `3` `4`

### 태스크 상태 변경
```bash
python3 hooks/state_manager.py focus \
  --domain {DOMAIN} \
  --task-id {TASK_ID} \
  --status {STATUS}
```

유효한 status 값: `none` `in_progress` `review` `blocked` `done`

### 전환 후 후속 작업
```bash
# 의미 있는 전환 시 git tag 생성
git tag neo/{DOMAIN}/{LIFECYCLE}/{YYYY-MM-DD}
git push origin neo/{DOMAIN}/{LIFECYCLE}/{YYYY-MM-DD}

# mem0 맥락 기록 (상태가 아닌 맥락)
# "NEO: {DOMAIN} {OLD}→{NEW}, 날짜: {YYYY-MM-DD}"
```

---

## 3. 변경 요청 (CR) 관리

### CR 생성
```bash
python3 hooks/state_manager.py cr-create \
  --id {CR_ID} \
  --title "{제목}" \
  --domains {도메인1} {도메인2} \
  --lifecycle {현재_LIFECYCLE} \
  --risk {low|medium|high}
```

CR ID 형식: `CR-001`, `CR-002` ...

### CR 승인 (사람이 승인 의사를 밝힌 후에만 실행)
```bash
python3 hooks/state_manager.py cr-approve --id {CR_ID}
```

### CR 종료
```bash
python3 hooks/state_manager.py cr-close --id {CR_ID}
```

---

## 4. 현재 상태 조회

```bash
# 세션 시작용 요약 출력
python3 hooks/state_manager.py summary

# 전체 상태 JSON 출력
python3 hooks/state_manager.py status
```

---

## 5. git을 통한 상태 이력 조회

`.neo_state.json`은 현재 상태만 담는다.
과거 상태와 전환 이력은 git이 보관한다.

### 활용 시점
1. **세션 재시작 시** — `last_updated`가 24시간 이상 경과한 경우
2. **에스컬레이션 보고 시** — 역방향 전환의 이전 상태 맥락 확보
3. **CR 발생 시** — 마지막 안정 상태(DEPLOYED) 커밋 특정
4. **상태 파일 손상 시** — 직전 정상 상태 복원

### 조회 명령어
```bash
# .neo_state.json 변경 이력 목록
git log --oneline -- .neo_state.json

# 특정 시점의 상태 내용 확인
git show {커밋해시}:.neo_state.json

# 최근 20개 이력 (날짜 포함)
git log --format="%h %ad %s" --date=short -20 -- .neo_state.json

# 의미 있는 체크포인트 목록
git tag | grep "neo/"

# 특정 도메인의 마지막 DEPLOYED 태그
git tag | grep "neo/{DOMAIN}/DEPLOYED"

# 손상 시 직전 커밋에서 복원
git checkout HEAD~1 -- .neo_state.json
```

### 에스컬레이션 보고 시 이력 포함 형식
```
"현재 {DOMAIN} 도메인의 Lifecycle 역행을 보고드립니다.
 이전 상태 이력:
   {git log 결과 요약 — 날짜·커밋·상태 변화}
 마지막 안정 시점: {날짜} ({커밋해시})
 그 이후 변경 사항: {변경 내용 요약}"
```

---

## 6. mem0 기록 원칙

### 기록하는 것
```
태스크 완료 후:
  → "NEO: {DOMAIN} 마지막 작업 {YYYY-MM-DD}"
  → tasks.md: [ ] → [x]

아키텍처 결정 시:
  → "AC: {결정 내용 — 한 줄 요약}"

도메인 전환 시:
  → "NEO: {OLD_DOMAIN}→{NEW_DOMAIN} 전환"

학습 기록:
  → "LEARN: [관찰] {패턴}
            [원인] {근본 원인}
            [수정] {어떻게 고쳤는가}
            [예측] {다음에도 효과적일 것이다}
            [검증] {다음 유사 태스크에서 확인}"
```

### 기록하지 않는 것
```
× "NEO: {DOMAIN} Phase=3, 완료=[T001], 진행중=T002"
× "NEO: Phase" 또는 Lifecycle 상태
× task_status (in_progress / done / blocked)

구조적 상태는 .neo_state.json이 SSoT다.
```

---

## 7. 칸반 운영

```
세션 시작:
  hermes kanban show (또는 http://127.0.0.1:9119)    ← 최우선
  BLOCKED 태스크 우선 확인

Lifecycle 전환 시점별 칸반 태스크:
  REQUIREMENTS → DESIGN:     QA 감리 칸반 태스크 생성
  DESIGN → IMPLEMENTATION:   QA 감리 칸반 태스크 생성
  Task Brief 완성:            구현 칸반 태스크 생성
  구현 완료:                  리뷰 칸반 태스크로 이동
  리뷰 완료:                  kanban_complete

BLOCKED 규칙:
  즉시 kanban_block → 사람 알림
  같은 BLOCKER 3회 → Phase 0 재진입 권고

issues/ 이슈 연동:
  복잡한 설계 결정 → project/docs/issues/{날짜}-{이슈}.md 생성
  칸반 태스크 --body에 파일 경로 연결
  종료 → project/docs/archive/issues/ 이동 + project/docs/design/decisions.md 반영
```

---

## 완료 후

스킬 파일 언로드.
