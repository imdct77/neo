---
name: badcase-distill
description: 프로젝트 완료 시 전체 BADCASE 증류 분석. 효과 있는 규칙만 장기 반영.
triggers:
  - MVP 완성 후
  - 프로젝트 최종 완료 시
---

# ⚠️ 이 파일은 Hermes 내장 스킬이 아닙니다. NEO가 조건에 따라 직접 읽어 따르는 Neo V1 참조 문서입니다.

# badcase-distill — 프로젝트 단위 학습 증류

## Step 1. 전체 BADCASE 조회

mem0에서 프로젝트 전체 BADCASE 조회:
  검색: "[{PROJECT_ID}] BADCASE:"
  검색: "[{PROJECT_ID}] BADCASE_RULE:"
  검색: "[{PROJECT_ID}] BADCASE_REVIEW:"

## Step 2. 규칙 효과 검증

`badcase-review.md`에서 도메인별로 추가된 규칙들의 효과를 검증한다.

```
각 BADCASE_RULE에 대해:
  이 규칙 적용 후, 같은 ACTOR+ORIGIN_PHASE+ERROR_TYPE이 재발했는가?

  재발 없음 → EFFECTIVE (효과 확인)
  재발 있음 → INEFFECTIVE (효과 없음)
  데이터 부족 → UNVERIFIED (검증 불가)
```

## Step 3. 규칙 분류

```
EFFECTIVE 규칙:
  → SOUL.md 또는 AGENTS.md 영구 반영 검토
  → 사람에게 승인 요청 후 반영

INEFFECTIVE 규칙:
  → 프롬프트 강제 → 코드 강제 격상 검토
  → 코드 강제도 어렵다면 → 설계 자체 재검토

UNVERIFIED 규칙:
  → 다음 프로젝트까지 유보
  → 현재 위치에 그대로 유지

과잉 규칙 (규칙이 너무 많아 LLM 부담):
  동일 목적의 규칙 통합
  더 이상 해당 패턴이 발생하지 않는 규칙 제거
```

### SCOPE 재평가

프로젝트 전체 데이터를 보면 도메인 단위에서는 보이지 않던 패턴이 드러난다.
SCOPE=DOMAIN으로 저장된 규칙이 실제로 여러 도메인에서 반복됐다면 CROSS로 승격한다.
(badcase-review.md Step 5에서 즉시 승격이 이미 처리됐을 수 있으나,
 전체 프로젝트 관점에서 재평가한다.)

```
SCOPE 재평가 기준:
  SCOPE=DOMAIN으로 저장된 규칙 중
  2개 이상의 도메인에서 같은 ACTOR+ERROR_TYPE 패턴이 발생했으면
    → SCOPE를 CROSS로 승격
    → mem0 기록 갱신:
      "[{PROJECT_ID}] BADCASE_RULE: ... | SCOPE:CROSS | ... (승격: DOMAIN→CROSS)"
    → 보고에 포함: "SCOPE 승격: {규칙 요약} DOMAIN→CROSS"
```

## Step 4. 격상 후보 식별

프롬프트 강제로 운영 중인 규칙 중 코드 강제로 격상할 후보를 찾는다.

```
격상 기준:
  INEFFECTIVE (프롬프트 강제 후에도 재발)
  + BLAST_RADIUS = CROSS 또는 SYSTEM
  + ERROR_TYPE ≠ QA_FALSE_POSITIVE (QA 오진은 코드 강제 불가)

→ forbidden-check.py에 파일 경로 패턴 차단 규칙 추가 검토
→ 사람에게 격상 제안
```

## Step 5. QA 오진 패턴 장기 반영

프로젝트 전체에서 QA_FALSE_POSITIVE / QA_FALSE_NEGATIVE 패턴을 harness/personas/qa.md에 반영한다.

```
FP 패턴: "QA가 {도메인}에서 {설계 패턴}을 오류로 지적한 사례 {N}건"
  → harness/personas/qa.md §3 해당 시점 체크리스트에
    "이 프로젝트의 {설계 패턴}은 의도된 설계입니다 — 오류로 판단하지 않습니다" 추가

FN 패턴: "QA가 {ERROR_TYPE}을 놓친 사례 {N}건"
  → harness/personas/qa.md §3 해당 시점 체크리스트에 해당 항목 추가
```

## Step 6. 사람에게 최종 보고

```
"[{PROJECT_NAME}] 전체 BADCASE 증류 완료

전체 규칙 현황:
  총 추가된 규칙: {N}건
  EFFECTIVE (효과 확인): {M}건
  INEFFECTIVE (효과 없음): {K}건
  UNVERIFIED (검증 불가): {J}건

장기 반영 권장 규칙 ({M}건):
  (사람 승인 요청)
  1. {규칙 요약} → SOUL.md §{섹션} 또는 AGENTS.md §{섹션}
  2. ...

코드 강제 격상 권장 ({K}건):
  (사람 승인 요청)
  1. {규칙 요약} → forbidden-check.py 차단 패턴 추가
  2. ...

SCOPE 승격 ({N}건):
  DOMAIN → CROSS로 승격된 규칙:
  1. {규칙 요약} — {N}개 도메인에서 재발 확인

제거 권장 규칙:
  1. {규칙 요약} — 이유: {더 이상 해당 패턴 미발생 / 중복}

QA 개선 사항:
  FP 패턴 {N}건 → harness/personas/qa.md 반영 완료
  FN 패턴 {M}건 → harness/personas/qa.md 반영 완료"
```

스킬 파일 언로드.
