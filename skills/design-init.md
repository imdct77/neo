---
name: design-init
description: 새 프로젝트 초기 설계 흐름 진입점. 첫 세션 감지 시 neo-start에서 자동 실행. 대화 방식 선택 → 아이디어 구체화 → 산출물 조건 충족 시 각 설계 스킬로 연결.
triggers:
  - 첫 세션 (mem0 기록 없음)
  - "새 프로젝트 시작"
  - "아이디어가 있어"
  - "설계부터 시작하자"
---


# ⚠️ 이 파일은 Hermes 내장 스킬이 아닙니다. NEO가 조건에 따라 직접 읽어 따르는 Neo 참조 문서입니다.

# design-init — 아이디어 구체화 및 설계 흐름 진입점

이 스킬은 진입점이다. 대화를 통해 아이디어를 구체화하고,
조건이 충족되면 각 설계 스킬을 순차적으로 실행한다.

```
design-init (이 파일)        ← 대화 진행, 조건 체크, 스킬 연결
  └→ design-arch.md          ← architecture.md 작성
  └→ design-db.md            ← database.md 작성 + 갱신 정책
  └→ design-api.md           ← api/ 협업 루프
  └→ design-screens.md       ← screens/ 작성 + tests 연동
```

---

## 소스 코드 위치

모든 구현 코드는 `src/be/`(백엔드)와 `src/fe/`(프론트엔드) 아래에 둔다.
하위 구조는 프로젝트의 기술 스택에 따라 BE·FE가 결정한다.
`setup.py` 실행 시 `src/be/`, `src/fe/` 디렉토리가 생성된다.

---

## Step 1. 인사 및 대화 방식 선택 (첫 세션 한정)

```
NEO:
  "안녕하세요! 오늘도 반짝이는 아이디어를 갖고 오신 CEO님, 반갑습니다.

   이제부터 아이디어에 대해 이야기를 나눠 볼까요?
   대화 진행 방식을 선택해 주세요.

   [1. 소크라테스식]
      NEO가 질문을 하나씩 드립니다.
      질문에 답하다 보면 자연스럽게 아이디어가 구체화됩니다.
      아직 아이디어가 막연하거나, 대화하면서 발견하고 싶을 때 추천합니다.

   [2. 초안 공유]
      생각하신 것을 자유롭게 말씀해 주세요.
      한 줄이어도 좋고, 길어도 좋습니다.
      말씀해 주신 내용을 바탕으로 NEO가 정리하고,
      부족한 부분은 질문을 통해 함께 채워나갑니다."
```

선택 후 mem0 저장: `"NEO: 대화방식={1|2}, 날짜={YYYY-MM-DD}"`

---

## Step 1-1. 제품 유형 기반 디자인 시스템 자동 추천 (첫 세션 한정)

대화 방식 선택 직후, NEO가 제품 유형을 물어보고 디자인 시스템을 자동 추천한다.

```
NEO:
  "멋진 아이디어를 갖고 오셨군요!
   먼저, 어떤 종류의 제품을 만드실 건가요?

   예를 들면:
   - '헬스케어 예약 앱이요'
   - 'B2B SaaS 대시보드예요'
   - '개발자 포트폴리오 사이트요'
   - '레스토랑 리뷰 플랫폼이에요'

   간단히 말씀해 주시면, 제품에 가장 잘 맞는 디자인 방향을 추천해 드릴게요."
```

### 자동 추천 프로세스

CEO의 답변을 받으면:

1. `harness/skills/templates/fe/product-design-map.md`에서 제품 유형 검색
   - 161개 제품 유형 중 키워드 매칭으로 최적 1~3개 후보 선별
2. 매칭된 유형의 **1차 스타일·컬러 팔레트·랜딩 패턴·대시보드 스타일** 추출
3. `product-design-map.md`의 **스타일 매핑 테이블**로 1차 스타일을 Neo 프리셋으로 변환
   - WARN 스타일(⚠️ Cyberpunk·3D Hyperrealism·Gen Z Chaos)이면 CEO에게 경고 + 대안 제시
4. Neo 프리셋의 HSL 변수를 `styling_design.md`에서 추출
5. 추천 결과를 CEO에게 제시:

```
NEO:
  "분석 결과, '{제품 유형}'에 가장 잘 맞는 디자인 방향입니다:

   🎨 스타일: Glassmorphism + Flat Design → Neo의 Soft Modern 프리셋
   🎨 대안:    Minimalism (Swiss 프리셋)
   🎯 컬러:    Trust blue + accent contrast → --primary: 211 100% 45%
   📐 레이아웃: Hero + Features + CTA
   📊 대시보드: Data-Dense + Real-Time Monitoring (해당 시)

   이 방향으로 진행할까요? 아니면 15개 프리셋 중 직접 선택하시겠습니까?"
```

5. CEO 승인 → 선택된 스타일의 CSS 변수 적용
6. CEO 거부 → 15개 프리셋 목록으로 폴백

### 키워드 매칭 실패 시

매칭되는 제품 유형이 없으면:

```
NEO:
  "정확히 일치하는 제품 유형을 찾지 못했어요.
   가장 가까운 카테고리에서 선택해 주시겠어요?

   [1. Tech & SaaS]      — B2B·개발자 도구·AI·클라우드
   [2. Finance]          — 금융·암호화폐·보험·회계
   [3. Healthcare]       — 의료·피트니스·정신건강
   [4. E-commerce]       — 쇼핑몰·구독·배달
   [5. Services]         — 뷰티·호텔·법률·예약
   [6. Creative]         — 포트폴리오·에이전시·게임
   [7. Lifestyle]        — 습관·명상·소셜·반려동물
   [8. Education]        — 학습·강좌·어학
   [9. Emerging Tech]    — Web3·IoT·AR/VR·로보틱스
   [10. 직접 스타일 선택]  — 15개 프리셋 목록으로 이동"
```

카테고리 선택 → 해당 카테고리 내 제품 유형 목록 제시 → 선택 → 스타일 추천.

### 예외 처리

- CEO가 "잘 모르겠다": 제품에 대해 2~3개 추가 질문 후 재시도
- CEO가 "추천 말고 직접 고를래요": 15개 프리셋 목록으로 즉시 이동
- CEO가 "나중에 할게요": 기본값(Bento)으로 진행, 언제든 Step 1-1 재실행 가능

선택 완료 후:
1. `harness/skills/templates/fe/styling_design.md`에서 해당 프리셋 CSS 변수 참조
2. `globals.css` `:root {}` 블록에 반영
3. Google Fonts import + `tailwind.config.ts` 등록
4. `harness/project.json`의 `design` 필드 갱신:
   ```json
   "design": {
     "product_type": "{매칭된 제품 유형}",
     "neo_preset": "{선택된 Neo 프리셋}",
     "color_palette": "{컬러 팔레트}",
     "font": "{폰트}",
     "landing_pattern": "{랜딩 패턴}",
     "selected_at": "{YYYY-MM-DD HH:MM:SS}"
   }
   ```
   → context-inject.py가 매 LLM 호출 전 이 정보를 컨텍스트에 주입
   → FE·BE가 구현 시 자신의 디자인 정보를 자동 확보
5. mem0 저장: `"NEO: 스타일={프리셋명}, 제품유형={매칭된 유형}, 날짜={YYYY-MM-DD}"`





---

## Step 1-2. 인프라 설정 — 인증·환경변수·gitignore (첫 세션)

Step 1-1 완료 후, NEO가 프로젝트 인프라 기본 설정을 진행한다.

### 1-2-1. 인증 방식 선택 (필요 시)

CEO의 아이디어에 사용자 계정·로그인이 필요하면:

```
NEO:
  "이 서비스에 사용자 인증이 필요할 것 같습니다.
   직접 JWT를 구현하는 대신, 관리형 인증 서비스 사용을 추천합니다.

   [1. Supabase Auth]  — PostgreSQL + Auth 내장. 1인 개발에 최적.
                        무료 티어 50,000 MAU. 소셜 로그인·매직 링크·MFA 내장.
   [2. Clerk]          — React 통합 최강. next-auth보다 세련된 UI 컴포넌트.
                        무료 티어 10,000 MAU.
   [3. Auth0]          — 엔터프라이즈급. 다양한 IdP 연동·규제 대응.
                        무료 티어 25,000 MAU.
   [4. Lucia Auth]     — 오픈소스·데이터베이스 기반. 직접 제어 원할 때.
                        무료. 직접 호스팅.
   [5. 직접 구현]      — JWT + bcrypt. 제어권 완전 확보.
                        단, 보안 구현 책임은 개발자에게.

   이 서비스의 규모와 요구사항에 가장 잘 맞는 것을 선택해 주세요.

   (지금 선택하지 않으면 Supabase Auth를 기본값으로 합니다.)"
```

CEO 선택 → AGENTS.md §2 기술 스택에 인증 방식 기록 → project.json에 `auth_provider` 추가.

인증이 필요 없으면 건너뛴다.

### 1-2-2. .env.example 자동 생성

NEO가 프로젝트 루트에 `.env.example` 템플릿을 생성한다:

```
NEO:
  ".env.example 파일을 생성했습니다.
   실제 API 키·비밀번호를 여기에 복사하고 .env로 저장하세요.

   .env.example에는 아래 항목이 포함됩니다:
   - DATABASE_URL
   - JWT_SECRET
   - {선택한 인증 서비스의 키}
   - S3 버킷·CloudFront URL (미디어 업로드 시)
   - DEBUG=False (프로덕션 기본값)

   .env는 절대 Git에 커밋하지 않습니다. (.gitignore에 등록됨)"
```

### 1-2-3. .gitignore 자동 생성

NEO가 프로젝트 루트 `.gitignore`를 생성한다:

```
기본 항목:
  .env
  .env.local
  .env.production
  node_modules/
  __pycache__/
  .next/
  dist/
  *.pyc

LLM 세션 보호 (Secure Vibe Coding 인용):
  .claude/
  .codex/
  .cursor/
  .hermes/sessions/
  .hermes/scratchpad/

AI가 실수로 세션 파일을 커밋하는 것을 방지한다.
```



```
대화 원칙:
  1. 질문 + 제안 + 진행 동의를 한 번의 응답에 함께 담는다
     예) "말씀하신 내용을 이렇게 이해했습니다. {정리}
          맞다면, 타겟 사용자는 누구인가요?
          이 방향으로 진행할까요?"

  2. 한 번의 응답에 질문은 하나만 한다

  3. AC 관점을 기본으로 하되, 필요 시 BE·FE로 전환하여
     기술적 실현 가능성과 화면 흐름을 함께 검토한다
```

---

## Step 3. 산출물 작성 시점 판단 — 체크리스트 기반

조건 충족 시 NEO가 작성을 제안한다.
거부 시 유형을 파악한다:

```
거부 유형 A: "아직 더 이야기하고 싶어"
  → 대화 계속. 조건 재충족 시 재제안.

거부 유형 B: "이 내용이 맞지 않아"
  → "어떤 부분이 맞지 않으셨나요?" 질문 후 수정.
     같은 내용으로 다시 제안하지 않는다.
```

### AGENTS.md 섹션 1·2 작성 조건
```
□ 서비스명이 확정됐는가?
□ 핵심 가치 제안(한 줄)이 나왔는가?
□ 타겟 사용자가 정의됐는가?
□ 백엔드·프론트엔드·DB 방향이 합의됐는가?
→ 모두 ✅: "프로젝트 개요와 기술 스택을 AGENTS.md에 기록할까요?"
```

### architecture.md 작성 조건
```
□ 전체 시스템 구성 요소가 논의됐는가?
□ 예상 트래픽·보안 요구사항이 한 번 이상 언급됐는가?
□ 배포 환경 방향이 합의됐는가?
→ 모두 ✅: "전체 아키텍처 문서를 작성할까요?"
   → harness/skills/design-arch.md 스킬 실행
```

### database.md 작성 조건
```
□ 핵심 엔티티 3개 이상이 명명됐는가?
□ 엔티티 간 관계가 논의됐는가?
□ 적어도 하나의 도메인이 확정됐는가?
→ 모두 ✅: "DB 설계 문서를 작성할까요?"
   → harness/skills/design-db.md 스킬 실행
```

### api/ 작성 조건
```
□ architecture.md가 확정됐는가?
□ database.md 초안이 있는가?
□ 첫 도메인의 핵심 API가 2개 이상 논의됐는가?
→ 모두 ✅: "API 설계 문서를 작성할까요?"
   → harness/skills/design-api.md 스킬 실행
```

### screens/ 작성 조건
```
□ api/ 초안이 있는가?
□ 핵심 화면 흐름이 한 번 이상 논의됐는가?
□ 복합 화면(ui_) 여부가 파악됐는가?
→ 모두 ✅: "화면 설계 문서를 작성할까요?"
   → harness/skills/design-screens.md 스킬 실행
```

### project/docs/requirements/{DOMAIN}.md 작성 조건
```
□ 도메인이 하나 이상 확정됐는가?
□ 핵심 시나리오 2개 이상이 논의됐는가?
□ 엣지 케이스가 한 번 이상 논의됐는가?
→ 모두 ✅: "{DOMAIN} 요구사항 문서를 작성할까요?"
   EARS 문법으로 작성 (WHEN/IF/WHILE/WHERE)
```

---

## Step 4. 초기 설계 완료 처리

모든 초기 설계 문서 작성 완료 시:
```
mem0 저장: "NEO: 초기 설계 완료, 날짜: {YYYY-MM-DD}"
mem0 저장: "NEO: 프로젝트 Phase=0 완료, 첫 도메인={DOMAIN}"
→ harness/works/workflow.md Phase 0로 진입
```

스킬 파일 언로드.
