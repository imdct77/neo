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

Q7. AI 생성 코드 보안 취약점 스캔 + STRIDE 위협 점검
    항상 해당 (매 게이트마다 실행):

    ### 7-1. 자동 스캔 (Git Hooks)
    Git Hooks(bandit·ESLint)가 커밋 시 자동 실행 중이면 "자동 처리"로 표시.
    Git Hooks가 없거나 추가 확인이 필요하면 수동 스캔으로 진행.

    ### 7-2. 수동 스캔 — 코드 레벨
      - 하드코딩된 시크릿 (API 키, 비밀번호, 토큰)
      - SQL Injection 취약 패턴 (raw query에 사용자 입력 직접 삽입)
      - 인증 우회 가능성 (get_current_user() Depends 누락)
      - 개인정보 로그 노출 (이메일·IP·토큰 평문 로깅)
      - CORS 설정 — Access-Control-Allow-Origin 와일드카드(*) 사용 여부
      - CSP 헤더 — Content-Security-Policy 설정 누락 또는 unsafe-inline·unsafe-eval 남용 여부
      - 의존성 취약점 — pip-audit·npm audit 결과 Critical·High 존재 여부
      - Shadow API — OpenAPI 스펙에 등록되지 않은 엔드포인트 존재 여부
      - AI 환각 패키지 — npm/PyPI에 존재하지 않는 패키지명 사용 여부

    ### 7-3. STRIDE 위협 모델링 — 신규 기능·API 기준
    Q1~Q6 중 하나라도 해당하는 경우(스택 변경·DB 변경·API 변경), STRIDE 6축 점검:

      S — Spoofing (위장)
        인증 토큰 위조·탈취 경로가 있는가?
        타 사용자 ID를 파라미터로 받아 권한 체크 없이 조회하는가?
      T — Tampering (변조)
        요청 본문·URL 파라미터가 중간에 변조될 가능성이 있는가?
        중요 데이터(가격·권한·상태)가 클라이언트 측에서 변조 가능한가?
      R — Repudiation (부인 방지)
        생성·수정·삭제 작업에 감사 로그가 남는가?
        결제·외부 발송 등 되돌릴 수 없는 작업의 수행자·시각이 기록되는가?
      I — Information Disclosure (정보 노출)
        에러 응답에 스택 트레이스·내부 경로·DB 구조가 노출되는가?
        민감 필드가 API 응답에서 제외되지 않고 반환되는가?
      D — Denial of Service (서비스 거부)
        무제한 페이지 크기·무제한 요청 횟수로 리소스 고갈 가능성이 있는가?
        대용량 업로드·재귀 쿼리·N+1 폭발로 DB 커넥션 풀이 고갈되는가?
      E — Elevation of Privilege (권한 상승)
        일반 사용자 엔드포인트로 관리자 작업을 수행할 수 있는가?
        role·permission 체크 없이 엔드포인트 접근이 가능한가?

    → 취약점 발견 시 AC! 전환. 수정 후 게이트 재진행.
    → STRIDE 점검은 신규 기능에 대해 최소 1회 수행. 기존 기능 수정 시 변경 범위만 점검.
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
