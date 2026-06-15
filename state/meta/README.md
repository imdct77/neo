# harness/state/meta/ — Neo 구현 메타 인덱스

소스 코드 탐색을 grep 대신 의미 기반으로 수행하기 위한 메타 인덱스 체계.

## 3계층 구조

| 계층 | 파일 | 목적 |
|------|------|------|
| L1 | `INDEX.md` | 디렉토리 내 파일·하위 디렉토리 목록. 항상 로드. |
| L2 | `DETAIL.md` | 디렉토리 개요 + 파일별 설계 의도. 판단 필요 시 로드. |
| L3 | `DETAIL.{파일명}.md` | 파일 단위 구현 상세. 수정·재사용 시에만 로드. |

## 디렉토리 구조

```
harness/state/meta/
  README.md                       ← 이 파일
  src/
    INDEX.md                      ← BE/FE 통합 진입점
    be/
      INDEX.md                    ← BE 최상위 디렉토리 목록
      {dir}/
        INDEX.md                  ← 디렉토리 내 파일·하위 디렉토리 목록
        DETAIL.md                 ← 디렉토리 개요 (필요 시)
        DETAIL.{filename}.md      ← 파일 상세 (필요 시)
    fe/
      INDEX.md                    ← FE 최상위 디렉토리 목록
      {dir}/
        INDEX.md
        DETAIL.md
        DETAIL.{filename}.md
```

## 생성 규칙

- 코드가 있는 모든 디렉토리는 INDEX.md를 갖는다.
- 공용 함수·컴포넌트가 발생하면 DETAIL.md를 생성.
- 파일 수정·재사용 판단이 필요할 정도로 복잡하면 L3 DETAIL.{파일명}.md 생성.
- `.template` 파일을 복사하여 생성. 템플릿은 프로젝트 진행 중 수정하지 않는다.

## 탐색 규칙

### 의미 기반 질의 (권장) — meta_search

구현 루프는 이 인덱스를 `meta_search`로 질의한다(수동 grep보다 먼저).

```
# 새 함수 작성 전 재사용 후보 확인 (DRY)
python3 harness/hooks/meta_search.py reuse-check --name {함수명} --desc "{설명}"

# 기능 영역 관련 코드 검색
python3 harness/hooks/meta_search.py search "{키워드}"
```

- `reuse-check`: 동일 이름·유사 이름(Levenshtein)·설명 겹침으로 재사용 후보를 랭크 제안.
- `search`: snake_case/camelCase 부분 토큰 + 한글 어간으로 의미 기반 검색.
- L3 상세가 채워진 함수만 색인된다(skeleton 제외) → 상세 완성도가 높을수록 강력.

### 수동 탐색 (보완)

meta_search가 비거나(미색인) 더 깊이 봐야 할 때:

1. `src/INDEX.md` → be/fe 선택
2. `be/INDEX.md` → 하위 디렉토리 목록
3. `{dir}/INDEX.md` → 파일 + 하위 디렉토리 목록
4. (필요 시) `DETAIL.md` → 파일별 설계 의도
5. (수정 시) `DETAIL.{파일명}.md` → 함수 상세

→ Neo 보고서 참조: `project/docs/issues/2026-06-09-구현-메타-인덱스-검토.md`
