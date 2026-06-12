---
name: design-db
description: database.md 작성 기준 + 갱신 정책. design-init에서 조건 충족 시 호출. AC 초안 → BE 검토 → AC 확정 순서로 진행.
triggers:
  - design-init에서 database.md 조건 충족 시
  - "DB 설계 문서 작성"
  - Q2(DB 스키마 변경) 게이트 통과 후 갱신
---


# ⚠️ 이 파일은 Hermes 내장 스킬이 아닙니다. NEO가 조건에 따라 직접 읽어 따르는 Neo V1 참조 문서입니다.

# design-db — database.md 작성 기준 + 갱신 정책

담당: AC 초안 → BE 검토 → AC 확정

---

## 작성 절차

```
Step 1. AC! → database.md 초안 작성
Step 2. BE! → 검토 의견 작성
  검토 관점:
    □ 누락된 인덱스 없는가?
    □ 트랜잭션 범위가 올바른가?
    □ .hermes.md Omission Constraints와 충돌 없는가?
    □ 마이그레이션 도구로 구현 가능한가?
Step 3. AC! → BE 의견 반영 → 확정
Step 4. NEO! → 사람에게 검토 요청
Step 5. 확정 후 mem0 저장:
  "AC: database.md 확정, 날짜: {YYYY-MM-DD}"
```

---

## 파일 위치

```
project/docs/design/database.md
```

---

## 포함 내용

```
## 도메인별 테이블 목록
  | 도메인 | 테이블 목록 |
  |--------|------------|
  | {DOMAIN} | {테이블1, 테이블2, ...} |

## 핵심 테이블 스키마
  테이블명:
    컬럼명 | 타입 | 제약 | 설명
    ------|------|------|-----
    id    | BIGSERIAL | PK | ...

  인덱스:
    - idx_{테이블명}_{컬럼명}: {목적}

  관계:
    - {테이블A}.{컬럼} → {테이블B}.{컬럼} (FK)

## 테이블 간 관계 요약 (ERD 텍스트)
  {DOMAIN_A}:
    users 1 ──< posts (1:N)
    posts N ──< tags (N:M via post_tags)

## DB 설계 원칙
  ### 소프트 딜리트 정책
    - 방식: {is_deleted 컬럼 | deleted_at 타임스탬프 | 별도 아카이브 테이블}
    - 적용 테이블: {목록}
    - 주의: {이 프로젝트 고유 소프트 딜리트 불변 원칙}

  ### 마이그레이션 정책
    - 도구: {Alembic | Flyway | Prisma Migrate | 기타}
    - 원칙: 마이그레이션 도구 없이 스키마 직접 변경 절대 금지

  ### 명명 규칙
    - 테이블: snake_case 복수형 (예: users, recipe_items)
    - 컬럼: snake_case (예: created_at, user_id)
    - 인덱스: idx_{테이블}_{컬럼} (예: idx_users_email)
    - FK: {참조테이블}_id (예: user_id)

## Omission Constraints (절대 금지)
  (.hermes.md DB 관련 항목과 동기화)
  - {프로젝트 고유 DB 절대 금지 항목}

## 변경 이력
  | 날짜 | 변경 내용 | 담당 | 이유 |
  |------|----------|------|------|
```

---

## 갱신 정책 (명확화)

```
갱신 트리거:
  Q2(DB 스키마 변경) 게이트 통과 후 반드시 갱신

갱신 책임:
  AC 초안 수정 → BE 검토 → AC 최종 확정
  (사람 승인 후 확정)

갱신 절차:
  1. AC! → 변경 내용 반영 (새 테이블·컬럼·인덱스·관계)
  2. BE! → 검토
     □ 인덱스 누락 없는가?
     □ 기존 쿼리 패턴과 충돌하는가?
     □ 마이그레이션 파일 생성 계획 있는가?
  3. AC! → 반영 → 변경 이력 추가
  4. mem0 저장:
     "AC: database.md 갱신, {변경 내용 한 줄}, {날짜}"

갱신 검증 체크리스트:
  □ 새 테이블에 인덱스가 포함됐는가?
  □ 소프트 딜리트 정책이 명시됐는가?
  □ .hermes.md Omission Constraints와 충돌하지 않는가?
  □ 마이그레이션 파일 생성 계획이 있는가?
  □ 도메인별 테이블 목록이 최신화됐는가?
  □ ERD 텍스트가 실제 스키마와 일치하는가?

절대 금지:
  - 변경 이력 삭제 금지
  - 마이그레이션 도구 없이 스키마 직접 변경 금지
  - BE 검토 없이 AC 단독 확정 금지 (DB는 BE 영역)
```

---

## Self-review 체크리스트

```
□ "TBD", "추후 결정" 표현 없음
□ 모든 테이블에 PK 명시
□ 모든 FK에 인덱스 존재
□ 소프트 딜리트 정책 일관성
□ 변경 이력 최신화
□ Omission Constraints 동기화
```

스킬 파일 언로드.
