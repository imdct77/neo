# 메타 인덱스 리팩토링 — 변경 매니페스트

이 패키지는 Neo 하네스 `neo-feat-substrate-first` 브랜치에, 메타 인덱스 검토 보고서의
구조 결함(F1·F2·F3·F4·F5)을 닫고 메타 인덱스 모델을 재정의한 작업을 반영한 것이다.

## 변경된 파일

### 코드 (hooks/)
- `meta_consistency_check.py` — 핵심 엔진. 아래 모두 반영:
  - **F1**: L3 함수 추출을 `## ...상세` 섹션으로 한정 + `주요 여부` 읽어 주요 함수만 중복 검사.
  - **F2**: L2 H1 인식을 em-dash/하이픈 모두 허용(`_detail_key_to_path`).
  - **F3**: 비코드 파일 제외(`_is_code_file`, 화이트리스트 `.py/.ts/.tsx/.js/.jsx/.mjs/.cjs`).
    네 수집 지점(sync walk·collect_actual_files·L2 검사·L3 integrity)에 일관 적용.
  - **F4**: 최상위 INDEX 함수 리네임 `sync_l3→sync_top_index` 등, 섹션 라벨을 청사진/구성/디테일로 정합.
  - **F5**: scope INDEX의 파일 평면 집계 제거. 각 디렉토리 INDEX는 직속 파일+직속 하위 디렉토리만.
  - **2a 보존 병합**: `_render_dir_index` — 구조는 결정론, LLM이 채운 의미는 보존(파일경로 키).
    타임스탬프 제거로 무변경 시 재기록 안 함.
  - **skeleton**: L3 skeleton을 scope `.template`에서 생성(`_write_l3_skeleton`).
  - 죽은 코드 7개 제거(약 −117줄): sync_l1·_regenerate_l1·_parse_sections·_file_to_section·
    _file_to_dir·_generate_section_index·_SECTION_INDEX_TEMPLATE.
- `meta_search.py` — `주요 여부` 필터(`primary_only`), BE/FE 양쪽 `## ...상세` 섹션 인식.
- `test_meta_skeleton.py`, `test_meta_search.py` — 회귀 테스트(skeleton 32 / search 18, 전부 통과).

### 템플릿 (state/meta/src/**/*.template)
- L1/L2/L3 해상도 사다리 정립(SoT=L3): L1 한 줄 투영 / L2 계약 요약 / L3 전체.
- 명칭·구조 통일: '하위 디렉토리', 컬럼 '목적', '링크' 컬럼. 디렉토리 목적 길이 제약 제거.
- L3 `주요 여부`(BE: API/export/event, FE: 네 경계 export·props-callback·API·route).
- 공용 요소 등급(전체 공용/도메인 공용) + L3 역방향 의존성(BE Imported by / FE 사용처).

### 스킬 (skills/)
- `meta-propagate.md` (신규) — (가) LLM 주도 전파 스킬. §4 전파 알고리즘(존재체크 grep→목적
  의미비교→승급), §4-5 공용 등급별 투영, **§5 공용 함수 수정·삭제 절대 절차**(여파 추적 강제).
- `README.md` — meta-propagate 인덱싱(스킬 표 + 트리거 흐름).

## 검증
- 전체 회귀: meta_skeleton 32 / meta_search 18 / neo_security 59 / neo_checks 50 — 전부 통과.
- `--sync`·`--check` 정상(비코드 오탐 0, 보존 병합 동작 실측 완료).

## ⚠️ 주의 — state/meta/src/ 의 생성 메타 9개 (테스트 잔재)
다음 파일은 작업 중 테스트로 생성된 **구포맷/혼재 상태의 잔재**이며, 실제 프로젝트의 메타가 아니다:
`INDEX.md`, `be/INDEX.md`, `be/models/{INDEX,DETAIL,DETAIL.__init__,DETAIL.user}.md`,
`be/services/{INDEX,DETAIL,DETAIL.auth}.md`.
일부는 신포맷 INDEX, 일부는 구포맷 L3로 일관성이 깨져 있다.
실제 사용 시 **삭제 후 `--sync`로 재생성**하거나 무시하라(`.template`은 최신이다).
임의 삭제로 인한 손실을 피하기 위해 이 패키지에는 그대로 남겨 두었다.
