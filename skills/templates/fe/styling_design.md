# 스타일링 — 설계 뷰 (AC용)

> **로드 시점**: Phase 0~2 (AC가 아키텍처 설계 시)
> **구현 코드**: `styling_impl.md` 참조

---

## CSS 방법론 — Tailwind 결정 이유

```
1. 컴포넌트와 스타일 공존 (Co-location)
   JSX와 동일 파일 내 className으로 스타일링 → 파일 전환 없음
   별도 CSS 파일 관리 불필요

2. 빌드 타임 최적화
   사용된 클래스만 번들링. 프로덕션 CSS는 수 KB
   전통 CSS의 사용하지 않는 스타일 누적 방지

3. 디자인 시스템 내장
   Tailwind 설정(shadcn/ui CSS 변수) = 디자인 토큰
   임의 값(arbitrary value)보다 토큰 기반 스타일링 유도

4. 반응형·다크모드 내장
   sm:/md:/lg: 브레이크포인트, dark: 접두사
   별도 미디어 쿼리·테마 전환 코드 불필요
```

**선택하지 않은 방법과 이유**:
- CSS-in-JS (styled-components, Emotion): 런타임 오버헤드. Next.js RSC와 충돌
- CSS Modules: Tailwind 대비 생산성 낮음. 컴포넌트 라이브러리(shadcn/ui) 비호환
- 순수 CSS: 유지보수 어려움. 디자인 시스템 적용에 수작업 필요

---

## 디자인 토큰 아키텍처

shadcn/ui CSS 변수를 디자인 토큰으로 사용한다. `globals.css`에 정의된 변수가 전체 앱의 디자인 언어를 결정한다.

```
CSS 변수 → Tailwind 클래스 → 컴포넌트
     ↑ 직접 사용 금지
     (Tailwind 클래스가 추상화 계층)
```

**토큰 계층**:

| 계층 | 예시 | 변경 범위 |
|------|------|---------|
| 프리미티브 | `--primary: 221.2 83.2% 53.3%` | 전체 앱 (globals.css) |
| 시맨틱 | `bg-primary`, `text-primary-foreground` | 유틸리티 클래스 |
| 컴포넌트 | `cn("rounded-lg border p-4", variant)` | 개별 컴포넌트 |

**규칙**:
- 프리미티브 토큰은 `globals.css`에만 정의한다
- 컴포넌트에서 `hsl(var(--primary))` 직접 사용 금지 → Tailwind 클래스로 접근
- 시맨틱 토큰 부족 시 `tailwind.config.ts` `extend`로 추가

---

## 반응형 설계 전략

**브레이크포인트**: Mobile-First 접근

```
sm: 640px   → 기본 모바일     (모바일은 접두사 없음)
md: 768px   → 태블릿
lg: 1024px  → 작은 데스크탑
xl: 1280px  → 데스크탑
```

**레이아웃 설계 기준**:

| 화면 | 레이아웃 전략 | 예시 |
|------|-------------|------|
| 모바일 (< md) | 단일 컬럼, 하단 네비게이션 | `flex-col` |
| 태블릿 (md~lg) | 2컬럼, 사이드바 축소/토글 | `md:flex-row` |
| 데스크탑 (> lg) | 멀티 컬럼, 전체 사이드바 | `lg:grid-cols-3` |

**컴포넌트 반응형 분기 기준**:
- 레이아웃: flex/grid의 `flex-col`/`grid-cols` 변경
- 크기: `w-full`/`md:w-1/2`/`lg:w-1/3` 패턴
- 타이포그래피: `text-xl`/`md:text-2xl`/`lg:text-3xl` 스케일
- 표시/숨김: `hidden md:block` (컴포넌트 단위 숨김)

---

## 다크 모드 설계

```
ThemeProvider (next-themes)
    → <html class="dark">
        → globals.css .dark {} 변수 오버라이드
            → 모든 Tailwind dark: 클래스 활성화
```

**설계 원칙**:
- 시스템 선호도 우선 (`defaultTheme="system"`)
- 수동 전환 가능 (ThemeToggle)
- `suppressHydrationWarning`으로 초기 깜빡임 방지
- 모든 컴포넌트는 기본적으로 라이트·다크 양쪽 대응

---

## 스타일링 경계

```
shadcn/ui 컴포넌트 (components/ui/)
    → 원본 수정 금지. 업데이트 시 덮어씌워짐
    → 커스터마이징: className prop + variant 확장

공통 컴포넌트 (components/common/)
    → shadcn/ui 컴포지션. 스타일 일관성 유지

도메인 컴포넌트 (components/{domain}/)
    → 공통 컴포넌트 조립. Tailwind 유틸리티 직접 사용 가능
```

**컴포넌트 스타일 노출 규칙**:
- 모든 컴포넌트는 `className` prop으로 외부 스타일 주입 허용
- `className`은 `cn()`으로 병합. 외부 주입이 항상 마지막 인자
- `style` prop 직접 사용 금지 (인라인 스타일은 Tailwind로 표현)

---

## Task 분리 기준

| 작업 | 위치 | 선행 조건 |
|------|------|---------|
| CSS 변수·Tailwind 설정 | `globals.css`, `tailwind.config.ts` | 없음 (선행) |
| shadcn/ui 기본 설치 | `npx shadcn-ui init` | 없음 (선행) |
| 공통 컴포넌트 스타일링 | `components/common/` | CSS 변수 완료 후 |
| 도메인 컴포넌트 스타일링 | `components/{domain}/` | 공통 컴포넌트 완료 후 |
| 반응형 대응 | 각 컴포넌트 내 className | 해당 컴포넌트 구현 시 병행 |
| 다크 모드 대응 | 각 컴포넌트 내 `dark:` 접두사 | 반응형 완료 후 |

---

## 주의: 설계에서 자주 발생하는 실수

- `globals.css`를 직접 편집하지 않고 컴포넌트에 인라인 HSL 작성 → 디자인 토큰 분열
- Tailwind 없이 순수 CSS 파일 병행 → 스타일 충돌·일관성 붕괴
- 반응형을 모바일 이후에 "추가" → Mobile-First 위반, 데스크탑에서 모바일로 내려갈 때 깨짐
- `h-` `w-`에 고정 px 값 사용 → `h-40` (160px) 등 토큰 기반 단위 사용할 것
- Tailwind `@apply` 남용 → 컴포넌트 추상화 대신 CSS 파일에 스타일 로직 이동됨

---

## 스타일 프리셋 (Style Presets)

> design-init 단계에서 CEO가 선택할 수 있는 15가지 디자인 방향.
> 각 프리셋은 `globals.css`에 복사 가능한 shadcn/ui CSS 변수 + Tailwind 폰트 설정을 제공한다.
> 프리셋은 출발점이다 — CEO의 브랜드에 맞게 수정할 수 있다.

### 사용 방법

1. design-init에서 CEO가 스타일 선택
2. 선택된 스타일의 CSS 변수를 `globals.css` `:root {}` 블록에 복사
3. Google Fonts import 추가
4. `tailwind.config.ts` `extend.fontFamily`에 폰트 등록

---

### 1. Bento — 애플풍 미니멀 그리드 (Apple-like Minimal)

> 깨끗하고 신뢰감 주는 애플 스타일. SaaS·크리에이터 도구에 적합.

```
Font:     Plus Jakarta Sans (400–800)
Radius:   --radius: 1.25rem (20px)
Shadows:  부드럽고 얕은 그림자. hover 시 살짝 떠오름
```

```css
--background: 0 0% 96%;       /* #f5f5f7 */
--foreground: 240 2% 10%;      /* #1d1d1f */
--primary: 211 100% 45%;       /* #0071e3 */
--primary-foreground: 0 0% 100%;
--secondary: 0 0% 94%;         /* #f0f0f0 */
--secondary-foreground: 240 2% 10%;
--muted: 240 5% 45%;           /* #6e6e73 */
--muted-foreground: 240 5% 65%;
--accent: 211 100% 45%;
--accent-foreground: 0 0% 100%;
--border: 0 0% 93%;
--radius: 1.25rem;
```

**적합**: 생산성 도구·대시보드·크리에이터 플랫폼

### 2. Soft Modern — 부드럽고 친근한 모던 (Friendly Modern)

> 흰 바탕에 흐릿한 오브 장식. 스타트업·소셜 플랫폼에 적합.

```
Font:     System-ui (Tailwind 기본)
Radius:   --radius: 0.75rem (12px)
Shadows:  단일 부드러운 그림자 (0 10px 30px)
```

```css
--background: 0 0% 100%;
--foreground: 222 47% 11%;      /* slate-900 */
--primary: 221 83% 53%;         /* blue-600 */
--primary-foreground: 0 0% 100%;
--secondary: 210 40% 96%;
--secondary-foreground: 222 47% 11%;
--muted: 215 16% 47%;           /* slate-500 */
--muted-foreground: 215 20% 65%;
--accent: 330 81% 60%;          /* pink-500 */
--accent-foreground: 0 0% 100%;
--border: 214 32% 91%;          /* slate-200 */
--radius: 0.75rem;
```

**적합**: 소셜 앱·커뮤니티·컨슈머 서비스

### 3. Scandinavian — 차가운 백색·극단적 여백 (Nordic Minimal)

> 북유럽 가구 같은 절제된 미학. 포트폴리오·디자인 도구·라이프스타일에 적합.

```
Font:     Sora 또는 Figtree (300–600). 제목도 medium까지만
Radius:   --radius: 0.25rem (거의 사각)
Shadows:  사용하지 않음. 공간과 여백이 시각적 계층을 만든다
```

```css
--background: 60 8% 97%;        /* #f9f9f7 warm white */
--foreground: 60 3% 10%;        /* #1c1c1a */
--primary: 24 45% 53%;          /* #c4854a terracotta */
--primary-foreground: 0 0% 100%;
--secondary: 40 5% 94%;
--secondary-foreground: 60 3% 10%;
--muted: 40 3% 53%;             /* #8a8880 */
--muted-foreground: 40 3% 65%;
--accent: 206 35% 55%;          /* #4a7fa5 slate blue */
--accent-foreground: 0 0% 100%;
--border: 42 6% 89%;
--radius: 0.25rem;
```

**적합**: 포트폴리오·갤러리·라이프스타일 브랜드

### 4. Corporate — 보수적 신뢰감의 B2B (Enterprise Trust)

> 구조화된 그리드·네이비 톤. B2B SaaS·금융·엔터프라이즈에 적합.

```
Font:     Source Sans 3 또는 IBM Plex Sans (300–700)
Radius:   --radius: 0.375rem (6px)
Shadows:  최소한. 그림자보다 테두리·구분선 사용
```

```css
--background: 0 0% 100%;
--foreground: 221 39% 11%;      /* gray-900 */
--primary: 212 45% 23%;         /* #1e3a5f navy */
--primary-foreground: 0 0% 100%;
--secondary: 214 33% 96%;       /* #f8f9fc */
--secondary-foreground: 221 39% 11%;
--muted: 220 9% 46%;            /* gray-500 */
--muted-foreground: 220 9% 60%;
--accent: 217 91% 60%;          /* blue-500 */
--accent-foreground: 0 0% 100%;
--border: 220 13% 91%;          /* gray-200 */
--radius: 0.375rem;
```

**적합**: B2B SaaS·금융·법률·엔터프라이즈 대시보드

### 5. Swiss — 헬베티카 타이포그래픽 (Typographic Purity)

> 흑·백·빨강만. 타이포그래피가 유일한 장식. 문서 중심·출판에 적합.

```
Font:     Inter (700 max, bold만 사용, black 금지)
Radius:   --radius: 0
Shadows:  없음. 모든 시각적 구분은 선·여백·폰트 웨이트로
```

```css
--background: 0 0% 100%;
--foreground: 0 0% 0%;
--primary: 0 0% 0%;             /* black */
--primary-foreground: 0 0% 100%;
--secondary: 0 0% 96%;          /* #f4f4f4 */
--secondary-foreground: 0 0% 0%;
--muted: 0 0% 40%;
--muted-foreground: 0 0% 55%;
--accent: 0 100% 45%;           /* #e60000 — 유일한 색상 */
--accent-foreground: 0 0% 100%;
--border: 0 0% 0%;
--radius: 0;
```

**적합**: 블로그·문서 플랫폼·출판·뉴스레터

### 6. Dark SaaS — 다크 모드 SaaS (Modern Dark)

> 진한 슬레이트에 스카이 블루 포인트. 개발자 도구·기술 SaaS에 적합.

```
Font:     System-ui (Tailwind 기본)
Radius:   --radius: 0.5rem (8px)
Shadows:  없음. 테두리와 배경 대비로 계층 구분
```

```css
--background: 229 84% 5%;       /* slate-950 #020617 */
--foreground: 210 40% 98%;      /* slate-100 */
--primary: 199 89% 48%;         /* sky-500 #0ea5e9 */
--primary-foreground: 229 84% 5%;
--secondary: 217 33% 17%;       /* slate-900 #0f172a */
--secondary-foreground: 210 40% 98%;
--muted: 215 20% 65%;           /* slate-400 */
--muted-foreground: 215 16% 47%;
--accent: 199 89% 48%;
--accent-foreground: 229 84% 5%;
--border: 217 33% 25%;          /* slate-800 */
--radius: 0.5rem;
```

**적합**: 개발자 도구·API 서비스·기술 블로그·CI/CD 대시보드

### 7. Dark Mono — 모노스페이스 다크 (Developer Aesthetic)

> 터미널 미학. 모든 텍스트 monospace. 개발자 포트폴리오·도구에 적합.

```
Font:     ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas
Radius:   --radius: 0.25rem (4px)
Shadows:  없음. 테두리로만 구분
```

```css
--background: 240 6% 4%;        /* #09090b zinc near-black */
--foreground: 0 0% 98%;         /* #fafafa */
--primary: 0 0% 98%;
--primary-foreground: 240 6% 4%;
--secondary: 240 5% 11%;        /* #18181b */
--secondary-foreground: 0 0% 98%;
--muted: 240 5% 45%;            /* #71717a */
--muted-foreground: 240 5% 55%;
--accent: 336 100% 65%;         /* cyan-hot pink pop */
--accent-foreground: 240 6% 4%;
--border: 240 4% 16%;           /* #27272a */
--radius: 0.25rem;
```

**적합**: 개발자 포트폴리오·터미널 앱·코드 공유 플랫폼

### 8. Luxury — 고급스러운 세리프 (Premium & Elegant)

> 크림 배경·세리프·골드 포인트. 럭셔리 브랜드·명품 커머스에 적합.

```
Font:     Cormorant Garamond 또는 Bodoni Moda (제목, 300–700) + Jost (본문)
Radius:   --radius: 0.25rem (4px)
Shadows:  없음. 여백과 타이포그래피로 품격 표현
```

```css
--background: 35 25% 95%;       /* #f8f4ef warm cream */
--foreground: 30 10% 10%;       /* #1c1917 */
--primary: 45 60% 37%;          /* #b8942a gold */
--primary-foreground: 0 0% 100%;
--secondary: 0 0% 100%;         /* white */
--secondary-foreground: 30 10% 10%;
--muted: 30 5% 45%;             /* #78716c */
--muted-foreground: 30 5% 55%;
--accent: 41 40% 52%;           /* #d4af6a light gold */
--accent-foreground: 30 10% 10%;
--border: 35 13% 85%;
--radius: 0.25rem;
```

**적합**: 럭셔리 커머스·호텔·프리미엄 예약 서비스·포트폴리오

### 9. Newspaper — 신문 편집 레이아웃 (Editorial Classic)

> 따뜻한 신문지 톤·세리프·잉크 느낌. 블로그·뉴스·매거진에 적합.

```
Font:     Playfair Display (제목, 400–900) + Source Serif 4 (본문)
Radius:   --radius: 0 (완전 사각)
Shadows:  없음. 구분선(rules)으로 섹션 분리
```

```css
--background: 36 23% 93%;       /* #f5f0e8 newsprint */
--foreground: 0 0% 10%;         /* #1a1a1a ink */
--primary: 0 0% 10%;
--primary-foreground: 36 23% 93%;
--secondary: 0 0% 100%;
--secondary-foreground: 0 0% 10%;
--muted: 30 4% 40%;             /* #6b6560 */
--muted-foreground: 30 4% 50%;
--accent: 6 63% 46%;            /* #c0392b red accent */
--accent-foreground: 0 0% 100%;
--border: 0 0% 10%;
--radius: 0;
```

**적합**: 뉴스·블로그·매거진·구독 뉴스레터

### 10. Blueprint — 청사진 기술 도면 (Technical Blueprint)

> 짙은 청색 배경·흰 격자·모노스페이스. 기술 문서·API 레퍼런스에 적합.

```
Font:     Courier Prime (400, 700, italic) — 전부 monospace
Radius:   --radius: 0
Shadows:  없음. 격자선이 구조를 만든다
```

```css
--background: 210 100% 20%;     /* #003366 blueprint blue */
--foreground: 208 100% 97%;     /* #F0F8FF alice blue */
--primary: 208 100% 97%;
--primary-foreground: 210 100% 20%;
--secondary: 210 100% 15%;      /* #002b55 darker panel */
--secondary-foreground: 208 100% 97%;
--muted: 208 30% 60%;
--muted-foreground: 208 30% 70%;
--accent: 50 100% 60%;          /* yellow annotations */
--accent-foreground: 210 100% 20%;
--border: 208 100% 97% / 0.15;  /* grid lines */
--radius: 0;
```

**적합**: API 문서·기술 명세·아키텍처 다이어그램·개발자 허브

### 11. Dashboard — 분석 대시보드 (Analytics & Admin)

> 고밀도 데이터·사이드바·차트 중심. 관리자 패널·분석 도구에 적합.

```
Font:     Inter (400–700). 숫자·ID는 monospace
Radius:   --radius: 0.375rem (6px)
Shadows:  최소한. 카드에만 subtle shadow
```

```css
--background: 210 40% 98%;      /* slate-50 #f8fafc */
--foreground: 217 33% 17%;      /* slate-800 #1e293b */
--primary: 217 91% 60%;         /* blue-500 #3b82f6 */
--primary-foreground: 0 0% 100%;
--secondary: 0 0% 100%;         /* white cards */
--secondary-foreground: 217 33% 17%;
--muted: 215 16% 47%;           /* slate-500 */
--muted-foreground: 215 20% 65%;
--accent: 162 47% 50%;          /* green-500 success */
--accent-foreground: 0 0% 100%;
--border: 214 32% 91%;          /* slate-200 */
--radius: 0.375rem;
--sidebar: 222 47% 11%;         /* dark sidebar #0f172a */
```

**적합**: 관리자 패널·분석 대시보드·데이터 시각화·CRM

### 12. Monolith — 흑백 브루탈 모노리스 (Bold Minimal)

> 흰 바탕·짙은 네이비 그림자·두꺼운 상단 강조선. 강한 브랜드 정체성에 적합.

```
Font:     System monospace (Tailwind font-mono). 제목 weight 900
Radius:   --radius: 0
Shadows:  offset shadow (navy), no blur. 그림자도 브루탈
```

```css
--background: 0 0% 100%;
--foreground: 221 39% 11%;      /* #111827 gray-900 */
--primary: 221 39% 11%;
--primary-foreground: 0 0% 100%;
--secondary: 0 0% 96%;
--secondary-foreground: 221 39% 11%;
--muted: 220 9% 46%;            /* gray-600 */
--muted-foreground: 220 9% 60%;
--accent: 0 0% 0%;              /* no color accents */
--accent-foreground: 0 0% 100%;
--border: 221 39% 11%;
--radius: 0;
```

**적합**: 크리에이티브 에이전시·패션·컬처 브랜드·포트폴리오

### 13. Organic — 자연 친화적 웜톤 (Natural & Earthy)

> 따뜻한 크림·테라코타·세이지 그린. 친환경·웰니스·로컬 비즈니스에 적합.

```
Font:     Fraunces (제목, 300–700) + DM Sans (본문, light weight)
Radius:   --radius: 0.75rem (12px) — 부드럽지만 과하지 않게
Shadows:  없음. 배경 색상 변화로 카드 구분
```

```css
--background: 36 25% 96%;       /* #faf7f2 warm cream */
--foreground: 36 20% 12%;       /* #2c2416 warm brown */
--primary: 16 48% 48%;          /* #c4623a terracotta */
--primary-foreground: 0 0% 100%;
--secondary: 33 18% 89%;        /* #f2ede4 tan */
--secondary-foreground: 36 20% 12%;
--muted: 30 15% 50%;            /* #8a7560 */
--muted-foreground: 30 15% 60%;
--accent: 96 16% 50%;           /* #6b8f6e sage green */
--accent-foreground: 0 0% 100%;
--border: 33 10% 82%;
--radius: 0.75rem;
```

**적합**: 웰니스·로컬 숍·친환경 제품·커뮤니티 플랫폼

### 14. Enterprise Editorial — 기업형 에디토리얼 (Bold Business)

> 밝고 어두운 섹션 교차·큰 앱 카드·인디고 포인트. 엔터프라이즈 SaaS 랜딩에 적합.

```
Font:     Inter (400–900). 제목 800–900 weight, 촘촘한 letter-spacing
Radius:   --radius: 1rem (16px) — 큰 카드용
Shadows:  없음. 배경 전환(white↔dark)으로 시각적 리듬
```

```css
--background: 0 0% 100%;
--foreground: 221 39% 11%;      /* gray-900 */
--primary: 239 84% 67%;         /* indigo-500 */
--primary-foreground: 0 0% 100%;
--secondary: 224 71% 4%;        /* gray-950 for dark sections */
--secondary-foreground: 210 40% 98%;
--muted: 220 9% 46%;
--muted-foreground: 220 9% 60%;
--accent: 239 84% 67%;
--accent-foreground: 0 0% 100%;
--border: 214 32% 91%;
--radius: 1rem;
```

**적합**: 엔터프라이즈 SaaS·비즈니스 플랫폼·대규모 서비스 랜딩

### 15. Dot Grid — 도트 그리드 + 핫 핑크 (Playful Technical)

> 회색 점 배경·Archivo Black 제목·핫핑크 포인트. 디자인 도구·창의적 SaaS에 적합.

```
Font:     Archivo Black (제목) + Space Mono (본문)
Radius:   --radius: 0.25rem (4px)
Shadows:  hard offset shadow (black, no blur) — 신문 만화 느낌
```

```css
--background: 220 14% 91%;      /* #e5e7eb gray-200 dotted */
--foreground: 0 0% 0%;
--primary: 0 0% 0%;
--primary-foreground: 0 0% 100%;
--secondary: 0 0% 100%;
--secondary-foreground: 0 0% 0%;
--muted: 220 5% 45%;
--muted-foreground: 220 5% 55%;
--accent: 340 86% 54%;          /* #F5276C hot pink */
--accent-foreground: 0 0% 100%;
--border: 0 0% 0%;
--radius: 0.25rem;
```

**적합**: 디자인 협업 도구·크리에이티브 SaaS·피드백 플랫폼

---

### 프리셋 선택 가이드

| 사용자 유형·제품 | 추천 프리셋 |
|----------------|-----------|
| 생산성 도구·SaaS | Bento / Soft Modern |
| B2B·엔터프라이즈 | Corporate / Enterprise Editorial |
| 개발자 도구·API | Dark SaaS / Dark Mono / Blueprint |
| 콘텐츠·미디어 | Newspaper / Swiss |
| 커머스·브랜드 | Luxury / Organic / Scandinavian |
| 분석·어드민 | Dashboard |
| 강한 개성·브랜드 | Monolith / Dot Grid |

> 출처: [claude-design-styles](https://github.com/chrismccoy/claude-design-styles) — 53개 스타일 중 Neo의 AI Aesthetic 회피 규칙을 통과한 15개 선별.
> 원본 스타일을 Tailwind/shadcn CSS 변수로 변환. CEO 브랜드에 맞게 HSL 값 조정 가능.
