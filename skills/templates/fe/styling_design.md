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
