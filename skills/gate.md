---
name: gate
description: 아키텍처 검토 게이트. Task Brief 전달 직전 자동 실행. Q1~Q7 더블 체크. Phase 0에서 놓친 위험 감지.
triggers:
  - Task Brief 생성 완료 시
  - "브리프 전달할게요" 직전
  - "구현 시작해줘" 직전
---


# ⚠️ 이 파일은 Hermes 내장 스킬이 아닙니다. NEO가 조건에 따라 직접 읽어 따르는 Neo V1 참조 문서입니다.

# gate — 아키텍처 검토 게이트 (더블 체크)

Task Brief를 전달하기 전에 반드시 이 스킬을 실행한다.
Phase 0에서 이미 검토했더라도 반드시 재확인한다.
Phase 0 이후 requirements·tasks 작성 중 새로운 위험이 추가됐을 수 있다.

## Q1~Q7 체크리스트

```
Q1. 기존에 없던 외부 시스템·라이브러리·서비스가 추가되는가?
    해당 예: 새 DB, 새 외부 API 연동, 새 패키지 추가
    → 해당 시: "스택 변경은 AGENTS.md에 명시된 기술 스택 외 추가입니다.
               AC 검토 후 승인이 필요합니다."

Q2. DB 스키마가 변경되는가?
    해당 예: 테이블 추가·수정·삭제, 인덱스 변경, ENUM 값 변경
    → 해당 시: Alembic migration 파일 포함 확인

Q3. 기존 API의 인터페이스가 변경되는가?
    해당 예: 엔드포인트·요청·응답 구조·상태코드 변경
    → 해당 시: FE↔BE 계약 업데이트 확인

Q4. 두 개 이상의 도메인에 영향을 주는가?
    해당 예: A 도메인이 B 도메인 테이블에 직접 접근
    → 해당 시: 도메인 경계 위반 여부 확인

Q5. 비가역적 작업인가?
    해당 예: 데이터 마이그레이션, 삭제, 결제, 외부 발송
    → 해당 시: 롤백 계획 확인

Q6. 성능·비용·보안에 직접 영향을 주는가?
    해당 예: Redis 전략 변경, 인증 방식 변경, 대용량 배치
    → 해당 시: 영향 범위 명시

Q7. AI 생성 코드 보안 취약점 스캔
    항상 해당 (매 게이트마다 실행):
    Git Hooks(bandit·ESLint)가 커밋 시 자동 실행 중이면 "자동 처리"로 표시.
    Git Hooks가 없거나 추가 확인이 필요하면 수동 스캔:
      - 하드코딩된 시크릿 (API 키, 비밀번호, 토큰)
      - SQL Injection 취약 패턴
      - 인증 우회 가능성
      - 개인정보 로그 노출
    → 발견 시 AC! 전환. 수정 후 게이트 재진행.
```

## 결과 처리

```
Q1~Q7 모두 해당 없음 (Q7 Git Hook 자동 처리 포함):
  "게이트 통과. Task Brief를 전달합니다."

Q1~Q6 하나 이상 해당 또는 Q7 수동 스캔 필요:
  → **doubt-driven 판단 (Doubt-Driven Decision)**: Q1~Q6 해당 건 중 아래 기준으로 판단:
    "이 결정이 틀리면 되돌리기 어려운가? (Is this decision hard to reverse if wrong?)"
    "NEO가 확신하지 못하는 영역인가? (Is this an area where NEO lacks confidence?)"
    하나라도 해당하면 `harness/skills/doubt-driven.md` 실행.
    CLAIM→EXTRACT→DOUBT→RECONCILE 사이클로 반증 검증.
  → AC! 로 전환 → ADR 형식으로 검토 결과 작성
  사람에게 보고 + 승인 요청
  승인 후 Task Brief에 ADR 포함하여 전달
  반려 시 대안 검토 후 재보고

Q7에서 수동 스캔이 필요한 경우:
  스캔 실행 → 이슈 발견 시 수정 후 게이트 재진행

칸반 연동:
  게이트 시작 시:
    /kanban create "{DOMAIN} 아키텍처 게이트"
      --assignee neo --tag gate
  게이트 통과:
    kanban_complete({id})
  게이트 BLOCKER:
    kanban_block({id}, "Q{N}: {이유}") → 사람 알림
```

## 완료 후

ADR이 작성됐으면 BADCASE 기록 (내부 검토 경로):
  Q1~Q7 게이트에서 이슈가 발견돼 ADR을 작성한 경우:
    mem0 저장:
      "BADCASE: AC | CONCERN | {도메인} | {이슈 요약} | {근본 원인} | {재발 방지} | 출처: 내부검토(gate) | {날짜}"

  이슈 없이 게이트 통과했으면: 넘어간다

이 gate 세션에서 스킬 흐름 자체에 문제가 있었는가?
  → 있으면: mem0 저장: "SKILL_ISSUE: gate — {문제} — {개선 제안}"
  → 없으면: 넘어간다

스킬 파일 언로드.
