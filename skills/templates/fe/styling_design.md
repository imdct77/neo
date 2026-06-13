1|# 스타일링 — 설계 뷰 (AC용)
2|
3|> **로드 시점**: Phase 0~2 (AC가 아키텍처 설계 시)
4|> **구현 코드**: `styling_impl.md` 참조
5|
6|---
7|
8|## CSS 방법론 — Tailwind 결정 이유
9|
10|```
11|1. 컴포넌트와 스타일 공존 (Co-location)
12|   JSX와 동일 파일 내 className으로 스타일링 → 파일 전환 없음
13|   별도 CSS 파일 관리 불필요
14|
15|2. 빌드 타임 최적화
16|   사용된 클래스만 번들링. 프로덕션 CSS는 수 KB
17|   전통 CSS의 사용하지 않는 스타일 누적 방지
18|
19|3. 디자인 시스템 내장
20|   Tailwind 설정(shadcn/ui CSS 변수) = 디자인 토큰
21|   임의 값(arbitrary value)보다 토큰 기반 스타일링 유도
22|
23|4. 반응형·다크모드 내장
24|   sm:/md:/lg: 브레이크포인트, dark: 접두사
25|   별도 미디어 쿼리·테마 전환 코드 불필요
26|```
27|
28|**선택하지 않은 방법과 이유**:
29|- CSS-in-JS (styled-components, Emotion): 런타임 오버헤드. Next.js RSC와 충돌
30|- CSS Modules: Tailwind 대비 생산성 낮음. 컴포넌트 라이브러리(shadcn/ui) 비호환
31|- 순수 CSS: 유지보수 어려움. 디자인 시스템 적용에 수작업 필요
32|
33|---
34|
35|## 디자인 토큰 아키텍처
36|
37|shadcn/ui CSS 변수를 디자인 토큰으로 사용한다. `globals.css`에 정의된 변수가 전체 앱의 디자인 언어를 결정한다.
38|
39|```
40|CSS 변수 → Tailwind 클래스 → 컴포넌트
41|     ↑ 직접 사용 금지
42|     (Tailwind 클래스가 추상화 계층)
43|```
44|
45|**토큰 계층**:
46|
47|| 계층 | 예시 | 변경 범위 |
48||------|------|---------|
49|| 프리미티브 | `--primary: 221.2 83.2% 53.3%` | 전체 앱 (globals.css) |
50|| 시맨틱 | `bg-primary`, `text-primary-foreground` | 유틸리티 클래스 |
51|| 컴포넌트 | `cn("rounded-lg border p-4", variant)` | 개별 컴포넌트 |
52|
53|**규칙**:
54|- 프리미티브 토큰은 `globals.css`에만 정의한다
55|- 컴포넌트에서 `hsl(var(--primary))` 직접 사용 금지 → Tailwind 클래스로 접근
56|- 시맨틱 토큰 부족 시 `tailwind.config.ts` `extend`로 추가
57|
58|---
59|
60|## 반응형 설계 전략
61|
62|**브레이크포인트**: Mobile-First 접근
63|
64|```
65|sm: 640px   → 기본 모바일     (모바일은 접두사 없음)
66|md: 768px   → 태블릿
67|lg: 1024px  → 작은 데스크탑
68|xl: 1280px  → 데스크탑
69|```
70|
71|**레이아웃 설계 기준**:
72|
73|| 화면 | 레이아웃 전략 | 예시 |
74||------|-------------|------|
75|| 모바일 (< md) | 단일 컬럼, 하단 네비게이션 | `flex-col` |
76|| 태블릿 (md~lg) | 2컬럼, 사이드바 축소/토글 | `md:flex-row` |
77|| 데스크탑 (> lg) | 멀티 컬럼, 전체 사이드바 | `lg:grid-cols-3` |
78|
79|**컴포넌트 반응형 분기 기준**:
80|- 레이아웃: flex/grid의 `flex-col`/`grid-cols` 변경
81|- 크기: `w-full`/`md:w-1/2`/`lg:w-1/3` 패턴
82|- 타이포그래피: `text-xl`/`md:text-2xl`/`lg:text-3xl` 스케일
83|- 표시/숨김: `hidden md:block` (컴포넌트 단위 숨김)
84|
85|---
86|
87|## 다크 모드 설계
88|
89|```
90|ThemeProvider (next-themes)
91|    → <html class="dark">
92|        → globals.css .dark {} 변수 오버라이드
93|            → 모든 Tailwind dark: 클래스 활성화
94|```
95|
96|**설계 원칙**:
97|- 시스템 선호도 우선 (`defaultTheme="system"`)
98|- 수동 전환 가능 (ThemeToggle)
99|- `suppressHydrationWarning`으로 초기 깜빡임 방지
100|- 모든 컴포넌트는 기본적으로 라이트·다크 양쪽 대응
101|
102|---
103|
104|## 스타일링 경계
105|
106|```
107|shadcn/ui 컴포넌트 (components/ui/)
108|    → 원본 수정 금지. 업데이트 시 덮어씌워짐
109|    → 커스터마이징: className prop + variant 확장
110|
111|공통 컴포넌트 (components/common/)
112|    → shadcn/ui 컴포지션. 스타일 일관성 유지
113|
114|도메인 컴포넌트 (components/{domain}/)
115|    → 공통 컴포넌트 조립. Tailwind 유틸리티 직접 사용 가능
116|```
117|
118|**컴포넌트 스타일 노출 규칙**:
119|- 모든 컴포넌트는 `className` prop으로 외부 스타일 주입 허용
120|- `className`은 `cn()`으로 병합. 외부 주입이 항상 마지막 인자
121|- `style` prop 직접 사용 금지 (인라인 스타일은 Tailwind로 표현)
122|
123|---
124|
125|## Task 분리 기준
126|
127|| 작업 | 위치 | 선행 조건 |
128||------|------|---------|
129|| CSS 변수·Tailwind 설정 | `globals.css`, `tailwind.config.ts` | 없음 (선행) |
130|| shadcn/ui 기본 설치 | `npx shadcn-ui init` | 없음 (선행) |
131|| 공통 컴포넌트 스타일링 | `components/common/` | CSS 변수 완료 후 |
132|| 도메인 컴포넌트 스타일링 | `components/{domain}/` | 공통 컴포넌트 완료 후 |
133|| 반응형 대응 | 각 컴포넌트 내 className | 해당 컴포넌트 구현 시 병행 |
134|| 다크 모드 대응 | 각 컴포넌트 내 `dark:` 접두사 | 반응형 완료 후 |
135|
136|---
137|
138|## 주의: 설계에서 자주 발생하는 실수
139|
140|- `globals.css`를 직접 편집하지 않고 컴포넌트에 인라인 HSL 작성 → 디자인 토큰 분열
141|- Tailwind 없이 순수 CSS 파일 병행 → 스타일 충돌·일관성 붕괴
142|- 반응형을 모바일 이후에 "추가" → Mobile-First 위반, 데스크탑에서 모바일로 내려갈 때 깨짐
143|- `h-` `w-`에 고정 px 값 사용 → `h-40` (160px) 등 토큰 기반 단위 사용할 것
144|- Tailwind `@apply` 남용 → 컴포넌트 추상화 대신 CSS 파일에 스타일 로직 이동됨
145|
146|---
147|
148|## 스타일 프리셋 (Style Presets)

> design-init 단계에서 CEO가 선택할 수 있는 15가지 디자인 방향.
> 각 프리셋은 개별 파일(`presets/{name}.md`)로 분리되어 있다.
> **design-init에서 선택된 프리셋만 로드**하여 컨텍스트를 최적화한다.

### 사용 방법

1. design-init에서 CEO가 스타일 선택
2. 선택된 스타일의 프리셋 파일을 로드 (`presets/{name}.md`)
3. CSS 변수를 `globals.css` `:root {}` 블록에 복사
4. Google Fonts import 추가
5. `tailwind.config.ts` `extend.fontFamily`에 폰트 등록

### 프리셋 인덱스

| 파일 | 프리셋 |
|------|-------|
| `presets/bento.md` | Bento |
| `presets/soft-modern.md` | Soft Modern |
| `presets/scandinavian.md` | Scandinavian |
| `presets/corporate.md` | Corporate |
| `presets/swiss.md` | Swiss |
| `presets/dark-saas.md` | Dark SaaS |
| `presets/dark-mono.md` | Dark Mono |
| `presets/luxury.md` | Luxury |
| `presets/newspaper.md` | Newspaper |
| `presets/blueprint.md` | Blueprint |
| `presets/dashboard.md` | Dashboard |
| `presets/monolith.md` | Monolith |
| `presets/organic.md` | Organic |
| `presets/enterprise-editorial.md` | Enterprise Editorial |
| `presets/dot-grid.md` | Dot Grid |

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