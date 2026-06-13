# 메타 인덱스 탐색 규칙 (Frontend)

> **로드 시점**: 신규 컴포넌트·훅·유틸을 만들거나 기존 컴포넌트·훅을 수정하기 전.
> 페르소나 `personas/frontend.md` §2-0에서 분리된 문서.
> `personas/frontend.md`를 로드한 후, 탐색이 필요한 작업 시작 시 이 파일도 함께 로드한다.

### 2-0. 구현 전 필수 확인 — "먼저 찾고, 그 다음 만든다"

새 컴포넌트·훅·유틸을 만들기 전, 그리고 기존 컴포넌트·훅을 수정하기 전 반드시 코드베이스를 탐색한다.
탐색의 목적은 **변경이 미치는 여파를 정확히 판단하여 더 옳은 방향으로 구현하는 것**이다.
특히 기능 확장과 유지보수에서 과거 설계 의도를 모르면 같은 실수를 반복하게 된다.

메타 인덱스 탐색은 **공간**(현재 코드베이스 구조)과 **시간**(git 히스토리) 두 축으로 이뤄진다:
- **공간 탐색**: L3·L2·L1을 읽어 "이 컴포넌트가 어디 의존하고, 수정 시 리렌더가 어디까지 전파되는가" 파악
- **시간 탐색**: 코드가 꼬였을 때 git log로 meta 변경 이력을 추적해 "왜 이렇게 설계됐는가" 발견

탐색은 `state/meta/src/fe/INDEX.md` 메타 인덱스를 통해 수행한다.

**경로 도출 규칙**: 작업 대상 소스 파일이 `project/src/fe/{section}/{filename}`일 때, 대응되는 메타 인덱스 파일은 다음과 같다.

`{section}` = 소스 파일이 위치한 `src/{scope}/` 이후의 디렉토리 경로
  예: `src/fe/components/Button.tsx` → `components`
  예: `src/fe/layout/sidebar/Menu.tsx` → `layout/sidebar`
`{stem}`   = 파일명에서 확장자를 뗀 이름 (예: `Button.tsx` → `Button`, `useAuth.ts` → `useAuth`)

| 계층 | 메타 인덱스 경로 |
|:---:|------|
| L3 | `state/meta/src/fe/{section}/DETAIL.{stem}.md` |
| L2 | `state/meta/src/fe/{section}/DETAIL.md` |
| L1 | `state/meta/src/fe/{section}/INDEX.md` |

예: `project/src/fe/components/Button.tsx` → {section}=`components`, {stem}=`Button`
  → L3: `state/meta/src/fe/components/DETAIL.Button.md`
  → L2: `state/meta/src/fe/components/DETAIL.md`
  → L1: `state/meta/src/fe/components/INDEX.md`

예: `project/src/fe/layout/sidebar/Menu.tsx` → {section}=`layout/sidebar`, {stem}=`Menu`
  → L3: `state/meta/src/fe/layout/sidebar/DETAIL.Menu.md`
  → L2: `state/meta/src/fe/layout/sidebar/DETAIL.md`
  → L1: `state/meta/src/fe/layout/sidebar/INDEX.md`

```
구현·수정 전 탐색 순서 (모든 경로는 state/meta/src/fe/ 기준):

1. state/meta/src/fe/INDEX.md 읽기 → 하위 디렉토리 목록 파악 (L1)
2. state/meta/src/fe/{section}/INDEX.md 읽기 → 파일 목록 + 공용 컴포넌트 확인 (L1)
3. 유사 컴포넌트·훅 발견 시:
   a. (필요 시) state/meta/src/fe/{section}/DETAIL.md 읽기 → 설계 의도 확인 (L2)
   b. 동일 기능이면 → 그것을 사용한다 (재구현 금지)
   c. 유사 기능이면 → 아래 패턴 적용 검토
4. 상수·타입은 INDEX.md의 공용 요소 목록에서 확인.
   같은 의미의 것이 이미 있으면 import해서 사용.
   없을 때만 새로 정의.
5. (컴포넌트·훅 수정·재사용 시) 반드시 state/meta/src/fe/{section}/DETAIL.{파일명}.md (L3)를 먼저 읽는다:
   a. Props·리렌더 전파·상태 흐름·의존성 확인
   b. "수정 시 영향" 필드 확인 → 연쇄 변경 범위 파악
   ⚠️  L3가 존재하지 않으면 불완전 탐색 상태다. 다음 fallback으로 진행한다:
   - L3 없음 → L2(DETAIL.md)로 fallback. 가용한 정보로 판단.
   - L2도 없음 → L1(INDEX.md) 수준에서 진행.
   - 수정 전 L3를 먼저 생성(`--sync` 또는 수동)하고 시작한다.
6. 없으면 → 신규 구현.
   **Task Brief의 완료 조건에 반드시 'meta 갱신 완료'를 포함한다.**
   `[AUTO] TODO` 마커가 L2·L3에 남아있으면 구현 완료로 간주하지 않는다.
7. 수정 완료 후 state/meta/src/fe/{section}/DETAIL.{파일명}.md 갱신 항목을 Task Brief에 포함.
   `--exit-code` 훅이 `[AUTO] TODO` 마커를 감지하면 커밋이 차단된다.
8. 작업 내용이 인증·로깅 등 BE/FE 공통 관심사일 경우,
   `harness/skills/templates/shared/` 디렉토리의 템플릿도 함께 확인.
   설계 시 `_design.md`, 구현 시 `_impl.md` 를 로드.

### 파일 생성·삭제 시 메타 인덱스 cascade

컴포넌트·훅·유틸 파일 생성과 삭제는 **무조건 L2 수정 트리거**다. 각 단계는 **하위 계층의 상태+내용을 들고 상위 계층을 검토**한다. L3→L2→L1→상위 순으로 전파.
모든 메타 파일 경로는 state/meta/src/fe/ 아래에 위치한다.

**파일 생성 시 (L3 신규 → L3 상태·내용을 들고 L2 검토):**
8. `--sync`가 state/meta/src/fe/{section}/DETAIL.{파일명}.md (L3)를 `[AUTO] TODO` skeleton으로 자동 생성한다.
   LLM의 역할: skeleton의 TODO를 의미 있는 내용(Props·리렌더·상태흐름·의존성)으로 채운다.
9. L3 내용을 기준으로 state/meta/src/fe/{section}/DETAIL.md 검토 → 파일 인덱스에 `# {file_path} — 상세` 항목 추가
   ⚠️  L2 DETAIL.md의 각 파일 항목은 반드시 `# src/fe/{section}/{filename} — 상세` 형식이어야 한다 (#8).
   이 포맷을 벗어나면 메타 일관성 검증(`--exit-code`)이 항목을 감지하지 못해 누락 오탐이 발생한다.
10. L2 변경 내용을 기준으로 state/meta/src/fe/{section}/INDEX.md 검토 → 파일 라인 추가
11. 변경된 L1 상태·내용을 들고 상위 state/meta/src/fe/의 INDEX.md·DETAIL.md 검토
    → `--sync`가 이 cascade(9~11)를 자동 수행한다.

**파일 삭제 시 (L3 제거 → L3 상태를 들고 L2 검토):**
12. 삭제 전 state/meta/src/fe/{section}/DETAIL.{파일명}.md (L3) 확인 → 의존성·리렌더 전파 확인
    → 이 컴포넌트·훅을 참조하는 다른 코드가 있는지 파악
13. 파일 삭제 후:
    a. state/meta/src/fe/{section}/DETAIL.{파일명}.md (L3) 삭제
    b. L3 삭제 상태를 기준으로 state/meta/src/fe/{section}/DETAIL.md 검토 → 파일 인덱스에서 항목 제거. 남은 파일 0건이면 L2 삭제 판정
    c. L2 변경 내용을 기준으로 state/meta/src/fe/{section}/INDEX.md 검토 → 파일 라인 제거. 남은 파일 0건이면 섹션 삭제 판정
    d. 변경된 L1 상태·내용을 들고 상위 state/meta/src/fe/의 INDEX.md·DETAIL.md 검토
    e. Task Brief "meta 갱신 항목"에 삭제분 반영

### 수정·삭제 중 문제 발생 시 — git 히스토리 시간 탐색

컴포넌트·훅 수정이나 삭제로 예상치 못한 연쇄 문제(리렌더 폭발, 상태 꼬임)가 발생하면,
메타 인덱스의 공간 탐색(L3→L2→L1)만으로는 부족하다.
**git 히스토리**를 통해 소스 코드와 메타 인덱스의 변경 이력을 시간축으로 교차 분석한다.

**시간 탐색 트리거 — 다음 중 하나라도 해당하면 발동한다 (#6):**
- 예상치 못한 연쇄 수정 발생 (A 수정했는데 B, C도 같이 깨짐)
- 동일 컴포넌트·훅이 여러 곳에 중복 구현된 것을 발견
- L2·L1 정보와 실제 코드의 의미적 불일치 감지 (meta는 A라는데 코드는 B)
- 수정 후 `--exit-code`가 예상보다 많은 불일치를 보고

> ⚠️  소스 코드는 `{PROJECT_ROOT}` (project repo), 메타 인덱스는 `{HARNESS_ROOT}` (harness repo)에 있다.
> 두 repo는 분리되어 있으므로 각 명령을 올바른 디렉토리에서 실행해야 한다.

14. 소스 코드의 git 히스토리 탐색:
    `cd {PROJECT_ROOT} && git log -- project/src/fe/{section}/{filename}`
    → 언제, 누가, 왜 변경했는지 파악

15. 메타 인덱스의 git 히스토리 탐색:
    `cd {HARNESS_ROOT} && git log -- state/meta/src/fe/{section}/`
    → L3·L2·L1이 언제, 어떤 설계 의도로 변경되었는지 파악

16. 두 시간축 교차 분석:
    a. 메타 인덱스의 변경 시점 = 컴포넌트 설계 의도가 바뀐 시점
    b. 소스 코드의 변경 시점 = 실제 구현이 바뀐 시점
    c. 둘의 불일치(meta는 갱신됐는데 코드는 안 바뀜, 혹은 반대)가 꼬임의 원인
    d. 불일치를 해소하는 방향으로 수정 — 설계 의도에 코드를 맞추거나,
       코드 변경을 설계 의도로 승격(meta 갱신)

> 메타 인덱스는 raw diff보다 읽기 쉽다. Props·리렌더 전파·상태 흐름이
> 명시되어 있어 "왜 바뀌었는가"를 코드 diff보다 빠르게 파악할 수 있다.
```

