# Styling Design — 시맨틱 디자인 토큰 + 스페이싱 스케일

> AI가 생성하는 UI는 전형적인 실패 패턴을 가진다.
> 이 문서는 FE 구현 시 반드시 준수해야 할 디자인 시스템 규칙을 정의한다.
> FE 페르소나(§8 AI Aesthetic 회피)와 함께 사용한다.

---

## 1. 시맨틱 컬러 토큰 (Semantic Color Tokens)

### 원칙
- 원색(purple·indigo·blue-600 등)을 직접 사용하지 않는다
- 시맨틱 토큰(`text-primary`, `bg-surface` 등)만 사용
- Tailwind 사용 시 `theme.extend.colors`에 토큰 정의

### 필수 토큰

```
text-primary      → 본문 텍스트 (최소 4.5:1 대비)
text-secondary    → 보조 텍스트
text-muted        → 비활성·힌트 텍스트
text-inverse      → 어두운 배경 위 텍스트

bg-surface        → 페이지 배경
bg-elevated       → 카드·모달 배경
bg-overlay        → 모달 오버레이

border-default    → 기본 테두리
border-strong     → 강조 테두리

accent-primary    → 주요 인터랙티브 요소
accent-hover      → hover 상태
accent-active     → active·선택 상태

semantic-success  → 성공·완료
semantic-warning  → 경고
semantic-error    → 오류·삭제
semantic-info     → 정보·알림
```

### 금지
```
❌ text-purple-600    → ✅ text-accent-primary
❌ bg-indigo-500      → ✅ bg-accent-primary
❌ bg-gray-50         → ✅ bg-surface
❌ text-gray-900      → ✅ text-primary
❌ border-gray-200    → ✅ border-default
```

---

## 2. 스페이싱 스케일 (Spacing Scale)

### 원칙
- 0.25rem(4px) 기준 증분만 사용
- 임의 픽셀값(`13px`, `2.3rem` 등) 금지

### 허용 값

| Token | 값 | 용도 |
|-------|----|------|
| `space-1` | 0.25rem (4px) | 인라인 텍스트 아이콘 간격 |
| `space-2` | 0.5rem (8px) | 밀접한 요소 간격 |
| `space-3` | 0.75rem (12px) | 폼 필드 내부 패딩 |
| `space-4` | 1rem (16px) | 기본 요소 간격 |
| `space-6` | 1.5rem (24px) | 섹션 내 그룹 간격 |
| `space-8` | 2rem (32px) | 섹션 간격 |
| `space-12` | 3rem (48px) | 페이지 레벨 여백 |
| `space-16` | 4rem (64px) | 대형 레이아웃 여백 |

### 금지
```
❌ px-[13px]     ❌ py-[2.3rem]
❌ m-[7px]       ❌ gap-[22px]

✅ p-4 (1rem)    ✅ gap-6 (1.5rem)
```

---

## 3. 타이포그래피 계층 (Typography Hierarchy)

### 텍스트 크기 계층

| Token | 용도 |
|-------|------|
| `text-display` | 히어로·랜딩 제목 |
| `text-h1` | 페이지 제목 |
| `text-h2` | 섹션 제목 |
| `text-h3` | 서브섹션 제목 |
| `text-body-lg` | 강조 본문 |
| `text-body` | 기본 본문 |
| `text-body-sm` | 보조 정보·캡션 |
| `text-xs` | 라벨·메타 정보 |

### 원칙
- h1 → h2 → h3 → body 순서를 건너뛰지 않는다
- 정보 계층이 시각적 계층과 일치해야 한다
- 한 페이지 내 폰트 패밀리 2종류 이하

---

## 4. 보더 반경 계층 (Border-Radius Hierarchy)

### 원칙
- 모든 요소에 `rounded-2xl` 적용 금지
- 요소 유형별로 일관된 반경 사용

| 요소 유형 | 권장 값 |
|----------|---------|
| 버튼·입력 필드 | `rounded-md` (0.375rem) |
| 카드·모달 | `rounded-lg` (0.5rem) |
| 아바타·배지 | `rounded-full` |
| 체크박스·토글 | `rounded-sm` (0.125rem) |

---

## 5. 그림자 사용 규칙 (Shadow Guidelines)

### 원칙
- 과도한 그림자 금지 (`shadow-2xl`, `shadow-xl` 기본값 사용 금지)
- 그림자는 시각적 계층 표현 목적으로만 사용

| 용도 | 권장 값 |
|------|---------|
| 카드 (기본) | `shadow-sm` 또는 없음 |
| 카드 (hover) | `shadow-md` |
| 모달·드롭다운 | `shadow-lg` |
| 플로팅 액션 | `shadow-md` |

---

## 6. 콘텐츠 우선 레이아웃 (Content-First Layouts)

### 금지
```
❌ 제네릭 히어로 섹션 (아이콘 + 제목 + 설명의 3단 구성 반복)
❌ 로렘 입숨 플레이스홀더 (레이아웃 문제를 숨김)
❌ 주식형 카드 그리드 (모든 항목을 동일 크기 카드로 나열)
```

### 원칙
```
✅ 실제 콘텐츠 또는 현실적인 플레이스홀더 사용
✅ 정보 우선순위에 따른 레이아웃 (중요한 것이 먼저·크게)
✅ 목적 기반 레이아웃 (이 화면이 해결하는 사용자 문제는 무엇인가)
```

---

## 7. AI Aesthetic 체크리스트

구현 완료 후 아래 항목을 자가 점검한다:

- [ ] 원색(purple·indigo 등) 직접 사용 없음 — 시맨틱 토큰만 사용
- [ ] 과도한 그라디언트 없음 — 평면 또는 미묘한 수준
- [ ] `rounded-2xl` 남용 없음 — 요소별로 일관된 보더 반경
- [ ] 제네릭 히어로 섹션 없음 — 콘텐츠 우선 레이아웃
- [ ] 로렘 입숨 없음 — 실제 또는 현실적 플레이스홀더
- [ ] 과도한 패딩 없음 — 스페이싱 스케일 준수
- [ ] 주식형 카드 그리드 없음 — 목적 기반 레이아웃
- [ ] 과도한 그림자 없음 — 최소한의 시각적 계층 표현

---

## 참조

- `personas/frontend.md` §8 — AI Aesthetic 회피 원칙
- `harness/skills/gate.md` — 게이트 검증 단계
- 원본: `agent-skills/skills/frontend-ui-engineering/SKILL.md` — Avoid the AI Aesthetic
