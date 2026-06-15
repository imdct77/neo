# 다분기 탐색 — 데이터 구조 (스키마 v0.1)

> 근거: `docs/RESEARCH_multi-branch-exploration.md`. 이 문서는 그 연구의 데이터 구조 형식화다.
> SoT 원칙: **코드의 SoT는 git, 탐색 메타의 SoT는 이 레코드.** 코드를 복제하지 않고 git을 가리킨다.

---

## 1. 설계 원칙 (스키마가 따르는 결정들)

1. **코드 복제 금지 → git 참조**: 각 후보의 실제 코드는 git 브랜치/커밋에 있다. 레코드는
   해시만 든다. (메타 인덱스의 "SoT는 한 곳, 나머지는 투영"과 동일.)
2. **HISTORY 연결**: 분기점은 HISTORY 시간선의 한 지점. 레코드는 별도 파일(무겁고 구조적)이되,
   HISTORY에 "이 시점 다분기 탐색 → 레코드 링크"를 한 줄 남겨 시간선에서 발견 가능하게 한다.
3. **선제·사후 공유**: 한 레코드가 선제(처음부터 3~5개)와 사후(회귀 후 분기)를 모두 담는다.
   `trigger.mode`로만 갈리고 구조는 동일.
4. **2층 점수 벡터**: 결정론 층(측정만, reward hacking 앵커) + 루브릭 층(LLM-judge 채점).
5. **점수마다 '왜'(자연어) 필수**: 학습 신호이자 **융합 위험 분석의 입력**(강점의 출처).
6. **ancestry = 부모 목록**: 부모 1이면 변이/덜어냄, 부모 2+면 융합. 통합 표현.
7. **제시 = Pareto 집합 + 총합 1위**: 추천(총합 1위)을 주되 Pareto로 의심할 재료를 함께.
8. **융합 위험 분석은 지목 기반**(기본). 설정으로 자동 전체 전환 가능 `[설정 후보: 비용]`.
9. **안전 게이트**: 회귀 실행·후보 채택 등 파괴적 행위는 사용자 승인 필수. 설정 불가.

---

## 2. 스키마 (개념 — 필드 정의)

### exploration_record (한 분기 단위 = 한 탐색 세션)
| 필드 | 타입 | 설명 |
|---|---|---|
| `id` | string | 레코드 식별자 (예: `mbx-2026-0615-recipe-genealogy`) |
| `created_at` | date | 생성 시점 |
| `status` | enum | `exploring` / `awaiting_choice` / `decided` / `abandoned` |
| `trigger` | object | 발동 맥락 (아래) |
| `branch_point` | object | 분기점 (아래) |
| `rubric` | object | 이 탐색의 instance-specific 평가표 (아래) |
| `candidates` | array | 후보 구현들 (아래) |
| `presentation` | object | 사용자 제시 (Pareto + 총합 1위, 아래) |
| `decision` | object\|null | 선택 기록. 미결이면 null (아래) |

### trigger
| 필드 | 타입 | 설명 |
|---|---|---|
| `path` | enum | `structural`(메타 자동) / `semantic`(일방통행문 휴리스틱) / `human`(사람 지목) |
| `mode` | enum | `proactive`(선제) / `reactive`(사후=회귀) |
| `rationale` | string | 왜 이게 중요 결정인가 (일방통행문 서술) |
| `one_way_door` | string\|null | 해당하는 일방통행문 유형 (데이터모델/도메인모델/서비스경계/통신/인증/스택) |

### branch_point
| 필드 | 타입 | 설명 |
|---|---|---|
| `ancestor_commit` | string | 공통 조상 커밋 해시 (여기서 분기) |
| `history_ref` | string | HISTORY 항목 링크 (시간선의 어느 지점) |
| `problem` | string | 무엇을 결정하려는가 (문제 정의) |

### rubric (instance-specific — 이 탐색 전용 채점표)
| 필드 | 타입 | 설명 |
|---|---|---|
| `deterministic` | array | 결정론 항목 `{name, method}` — 측정만 (테스트통과·타입체크·meta정합·린트) |
| `judged` | array | 루브릭 항목 `{name, criterion, weight}` — LLM-judge 채점, 가중치 |
| `weights_approved_by` | enum | `neo_proposed` / `human_approved` — 가중치 승인 주체 (중요결정이므로 사람 확인 권장) |
| `judge_model` | string | 채점에 쓴 별도 모델 (자기선호 편향 분리) |

### candidate (후보 하나)
| 필드 | 타입 | 설명 |
|---|---|---|
| `id` | string | 후보 식별자 (예: `cand-A`) |
| `approach` | string | 접근 요약 (한두 줄) |
| `ancestry` | array | **부모 목록**. `[분기점]`=원변이, `[cand-A]`=A의 덜어냄, `[cand-A,cand-B]`=융합 |
| `git_ref` | string | 브랜치/커밋 참조 — 코드는 여기 (복제 안 함) |
| `scores` | object | 점수 벡터 (아래) |
| `pareto_status` | object | `{dominated: bool, wins_on: [축이름]}` — 어느 축에서 최고인가 |

### candidate.scores (2층 점수 벡터)
| 필드 | 타입 | 설명 |
|---|---|---|
| `deterministic` | array | `{name, result}` — 예 `{테스트, 12/12}`, `{타입체크, pass}` |
| `judged` | array | `{name, score, why, judge_model}` — **why=자연어 근거(강점 출처)** |
| `aggregate` | number\|null | 가중 총합 (judged 항목의 weight 적용). 자동 채택 후보 가리기용 |
| `position_calibrated` | bool | 위치 편향 보정(순열 집계) 적용 여부 |

### presentation (사용자에게 보여줄 형태)
| 필드 | 타입 | 설명 |
|---|---|---|
| `pareto_set` | array | Pareto-최적 후보 id 목록 (각자 어느 축 승자) |
| `top_aggregate` | string | 총합 1위 후보 id = **기본 추천** (정답 아님) |
| `tradeoffs` | string | "B 추천, 단 A는 성능·C는 견고성에서 앞섬" 식 요약 |
| `fusion_analyses` | array | 융합 위험 분석 — **지목 시에만 채워짐** (아래) |

### fusion_analysis (사용자가 쌍을 지목하면 네오가 생성)
| 필드 | 타입 | 설명 |
|---|---|---|
| `pair` | array | 지목된 후보 쌍 (예: `[cand-A, cand-B]`) |
| `apparent_benefit` | string | 얼핏 보이는 이점 (직관 인정) |
| `expected_risk` | string | 예상 위험 + **근거**(각 후보 강점의 출처 충돌. scores.judged.why에서 도출) |
| `acceptable_if` | string | 무엇을 덜 중시하면 감수할 만한가 (가치 위임 화법) |
| 비고 | — | 네오는 융합을 *결정/추천*하지 않는다. 위험을 인지시키고 판단은 사용자에게. |

### decision (선택 기록 — 학습 신호의 원천)
| 필드 | 타입 | 설명 |
|---|---|---|
| `method` | enum | `auto_winner`(총합 압도) / `user_choice` / `further_exploration`(융합·덜어냄 요청) |
| `chosen` | string\|null | 채택된 후보 id (further_exploration이면 null, 새 후보 생성으로 루프) |
| `reason` | string | **사용자가 왜 이걸 골랐나 (자연어)** — 가치 함수가 드러남 |
| `lesson` | string | 이 대조에서 배운 것 (GEPA식. 예: "이 도메인선 성능구조와 가독성 양립 불가") |
| `committed_as` | string\|null | 채택 후 최종 커밋 해시 (HISTORY와 연결) |

---

## 3. 선제 모드 — 예산·정지 조건·학습 신호

### 3-1. 예산: 왜 3~5개인가
AlphaEvolve·GEPA는 수백~수천 후보를 만들지만, 그건 *자동 평가가 깨끗한* 수학 도메인이라
가능하다. 우리는 후보마다 (a) 실제 구현 비용(3~5배), (b) 사람의 검토 인지비용이 든다.
사람이 의미 있게 비교 가능한 선택지는 3~5개가 한계(그 이상은 선택 마비). 즉 3~5는
기술적 최적이 아니라 **사람의 검토 한계에 맞춘 수**다.
- 개수보다 **다양성**이 중요: 비슷한 3개보다 접근이 다른 3개(AlphaEvolve MAP-elites의 niche).
- 규칙: 3~5개를 만들되 *접근이 충분히 다른* 것만. 비슷하면 줄이고 다양하면 늘린다(상한 5).
  `[설정 후보: 비용]` — 상한은 설정으로 조정 가능.

### 3-2. 정지 조건 (두 종류)
- **생성 정지**: 새 후보가 기존과 *다른 niche*를 못 채우면(접근이 이미 있는 것과 겹침) 생성 중단.
  "n개 채울 때까지"가 아니라 "다양성이 포화될 때까지".
- **루프 정지**(융합·추가 탐색, `further_exploration`): 새 후보가 Pareto를 개선 못 하면
  (비지배 추가 실패) "더 나아지지 않음"을 보고하고 멈춤. 매 바퀴 사용자 승인 게이트.
- 공통 원리: **"새로 만든 게 기존을 넘어서지 못하면 멈춘다"** = 무한 생성 방지 수렴 조건.
- ⚠ reward hacking 방어: 정지 판정은 "점수가 오르나"가 아니라 "**다양성·Pareto가 실질
  개선되나**"여야 한다. 점수만 보면 루프가 평가를 해킹하며 끝없이 돈다(연구노트 §3).

### 3-3. 학습 신호 (선택 → 미래 탐색)
진짜 학습(가중치 업데이트)은 불가. 우리가 하는 것은 **맥락 학습** — 과거 선택 기록을
미래 탐색의 입력으로 재사용한다. `decision`에 남길 것:
`{chosen, reason(왜 골랐나·자연어), lesson(배운 것·자연어), weight_correction(어느 축이 과/소평가됐나)}`

이 기록의 세 가지 재사용:
1. **다음 탐색의 후보 생성 편향**: "이 사용자/도메인은 단순성보다 성능을 일관되게 골랐다"
   → 다음 다분기에서 후보를 그쪽으로 편향 생성. (GEPA reflective feedback을 사용자 선택으로 구동.)
2. **루브릭 가중치 보정**: 사용자가 총합 1위를 제치고 다른 걸 골랐다면 "가중치가 사용자
   가치와 어긋남" → 다음엔 그 도메인 루브릭 가중치를 선택에 맞춰 조정. (사람 선택이 자동
   평가를 교정하는 held-out 신호 = reward hacking 방어와 연결.)
3. **mem0·HISTORY 적재**: `lesson`은 mem0(학습 메모리)에, 탐색 레코드는 HISTORY가 가리킴.
   → 다음 phase0 "탐색 대상 3(과거 내력)"에서 *과거의 탐색·선택*도 조회 대상이 됨
   ("이 도메인서 전에 이런 분기를 했고 사용자가 이걸 골랐다"를 보고 시작).

> "학습"은 모델이 아니라 *축적된 선택 기록이 미래 탐색을 형성하는 루프*다.
> 이 루프는 사용자 선택이 쌓여야 의미가 생기므로, 실사용 데이터 없이는 검증되지 않는다.

---

## 4. 예시 — JiggleBoggle 레시피 계보 DB (실제 사례로 채움)

> 사용자의 실제 사례: 레시피에 Git식 버전관리(분기·병합·계보)를 도입하는 DB 설계.
> 공용/전파/경계와 무관하나 **데이터 모델 = 일방통행문 → semantic 트리거**. 데이터가 쌓이면
> 마이그레이션 불가역.

```yaml
id: mbx-2026-0615-recipe-genealogy
status: awaiting_choice
trigger:
  path: semantic
  mode: proactive
  rationale: "레시피 계보를 RDB로 설계. 데이터 누적 후 스키마 변경은 마이그레이션 불가역."
  one_way_door: 데이터모델
branch_point:
  ancestor_commit: a1b2c3d
  history_ref: "HISTORY.md#2026-06-15-recipe-schema"
  problem: "분기·병합·계보 추적을 어떤 관계형 모델로 표현할 것인가"
rubric:
  deterministic:
    - {name: 계보쿼리 정확성, method: "조상/자손 조회 테스트 케이스"}
    - {name: 마이그레이션 가역성, method: "스키마 변경 시나리오 dry-run"}
  judged:
    - {name: 계보쿼리 성능, criterion: "깊은 계보에서 조회 비용", weight: 0.3}
    - {name: 병합 표현력, criterion: "다중 부모 병합을 자연히 표현하나", weight: 0.4}
    - {name: 스키마 단순성, criterion: "테이블·조인 복잡도", weight: 0.3}
  weights_approved_by: human_approved
  judge_model: "별도 모델"
candidates:
  - id: cand-A
    approach: "인접 리스트 (parent_id FK 단일 컬럼)"
    ancestry: [branch_point]
    git_ref: "branch/mbx-A@e4f5g6h"
    scores:
      deterministic: [{name: 계보쿼리 정확성, result: pass}, {name: 마이그레이션 가역성, result: pass}]
      judged:
        - {name: 계보쿼리 성능, score: 4, why: "깊은 계보는 재귀 CTE로 N회 조인 — 깊이에 비례해 느림", judge_model: 별도}
        - {name: 병합 표현력, score: 3, why: "단일 parent_id라 다중 부모 병합을 표현 못 함 — 병합이 핵심인데 치명적", judge_model: 별도}
        - {name: 스키마 단순성, score: 9, why: "테이블 1개·컬럼 1개. 가장 단순", judge_model: 별도}
      aggregate: 4.8
    pareto_status: {dominated: false, wins_on: [스키마 단순성]}
  - id: cand-B
    approach: "클로저 테이블 (조상-자손 쌍을 별도 테이블에 모두 저장)"
    ancestry: [branch_point]
    git_ref: "branch/mbx-B@i7j8k9l"
    scores:
      deterministic: [{name: 계보쿼리 정확성, result: pass}, {name: 마이그레이션 가역성, result: pass}]
      judged:
        - {name: 계보쿼리 성능, score: 9, why: "조상/자손이 단일 조인 — 깊이 무관 빠름", judge_model: 별도}
        - {name: 병합 표현력, score: 8, why: "다중 부모를 쌍으로 자연히 표현. 병합 친화적", judge_model: 별도}
        - {name: 스키마 단순성, score: 5, why: "별도 클로저 테이블·삽입 시 조상 전체 갱신 필요", judge_model: 별도}
      aggregate: 7.4
    pareto_status: {dominated: false, wins_on: [계보쿼리 성능, 병합 표현력]}
presentation:
  pareto_set: [cand-A, cand-B]
  top_aggregate: cand-B
  tradeoffs: "B 추천(성능·병합 표현력 우위). 단 A가 스키마 단순성에선 앞섬."
  fusion_analyses: []   # 사용자가 쌍을 지목하면 채워짐
decision: null
```

### 사용자가 "A와 B 합치면?" 지목 시 생성될 fusion_analysis 예
```yaml
pair: [cand-A, cand-B]
apparent_benefit: "A의 단순한 스키마 + B의 빠른 계보 쿼리를 합치면 단순하면서 빠를 것 같다."
expected_risk: "B의 성능은 '클로저 테이블에 조상 쌍을 모두 저장'에서 나온다(why 참조).
  A의 단순성은 '그 테이블이 없음'에서 나온다. 둘은 같은 자원을 정반대로 다뤄 양립 불가 —
  클로저 테이블을 넣으면 A의 단순성이 사라지고, 빼면 B의 성능이 사라진다. 융합 결과는
  '어정쩡한 중간'이 되기 쉽다."
acceptable_if: "계보 쿼리 성능을 높게 치지 않는다면(읽기보다 쓰기가 압도적이라면)
  A로 충분하다. 성능이 중요하면 단순성을 포기하고 B를 그대로 쓰는 게 융합보다 낫다."
```
