# 스타일링 — 구현 뷰 (FE용)

> **로드 시점**: Phase 3 Task Brief 작성 시 (FE 구현)
> **스택**: Tailwind CSS v3 / shadcn/ui / Next.js

---

## cn() 헬퍼 — 조건부 클래스 병합

```typescript
// lib/utils.ts (shadcn 기본 제공)
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

```tsx
// 사용 패턴
<div
  className={cn(
    "rounded-lg border p-4",           // 기본 클래스
    isActive && "border-primary",       // 조건부 클래스
    isDisabled && "opacity-50 cursor-not-allowed",
    className,                          // 외부 주입 클래스 (항상 마지막)
  )}
/>
```

---

## shadcn 테마 커스터마이징 (globals.css)

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    /* shadcn/ui CSS 변수 — 라이트 테마 */
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --primary: 221.2 83.2% 53.3%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 221.2 83.2% 53.3%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    /* ... 다크 테마 변수 */
  }
}
```

---

## 컴포넌트 변형(variant) 패턴 — cva 사용

```tsx
// components/common/StatusBadge.tsx
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold",
  {
    variants: {
      status: {
        pending:   "bg-yellow-100 text-yellow-800",
        confirmed: "bg-blue-100 text-blue-800",
        shipped:   "bg-purple-100 text-purple-800",
        delivered: "bg-green-100 text-green-800",
        cancelled: "bg-red-100 text-red-800",
      },
    },
    defaultVariants: {
      status: "pending",
    },
  }
);

interface StatusBadgeProps extends VariantProps<typeof badgeVariants> {
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const labels: Record<string, string> = {
    pending: "대기중", confirmed: "확인됨",
    shipped: "배송중", delivered: "배송완료", cancelled: "취소됨",
  };

  return (
    <span className={cn(badgeVariants({ status }), className)}>
      {labels[status ?? "pending"]}
    </span>
  );
}
```

---

## 반응형 레이아웃 패턴

```tsx
// Tailwind 브레이크포인트: sm(640) md(768) lg(1024) xl(1280)

// 반응형 그리드
<div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
  {items.map(item => <Card key={item.id} />)}
</div>

// 반응형 사이드바 레이아웃
<div className="flex flex-col md:flex-row min-h-screen">
  <aside className="w-full md:w-64 shrink-0">
    <Sidebar />
  </aside>
  <main className="flex-1 overflow-auto p-4 md:p-8">
    {children}
  </main>
</div>

// 반응형 타이포그래피
<h1 className="text-xl font-bold sm:text-2xl lg:text-3xl">
  제목
</h1>
```

---

## 다크 모드 패턴

```tsx
// app/layout.tsx — 다크 모드 클래스 적용
import { ThemeProvider } from "@/components/common/ThemeProvider";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <body>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
```

```tsx
// components/common/ThemeToggle.tsx
"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
    >
      <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
    </Button>
  );
}
```

---

## Tailwind 클래스 작성 규칙

```
순서 (자동화: prettier-plugin-tailwindcss):
  1. 레이아웃 (flex, grid, block)
  2. 위치 (relative, absolute)
  3. 크기 (w-, h-, max-w-)
  4. 여백 (m-, p-)
  5. 배경/테두리 (bg-, border-, rounded-)
  6. 텍스트 (text-, font-)
  7. 효과 (shadow-, opacity-)
  8. 반응형 (sm:, md:, lg:)
  9. 다크 모드 (dark:)
  10. 상태 (hover:, focus:, disabled:)
```

```tsx
// 올바른 순서 예시
<div className="flex items-center gap-2 w-full px-4 py-2 bg-background border rounded-md text-sm hover:bg-accent dark:border-border">
```

---

## AI Aesthetic 회피 (Avoid the AI Aesthetic)

> AI가 생성한 UI는 전형적인 실패 패턴이 있다.
> 아래 규칙은 Tailwind·shadcn/ui 사용 시 특히 주의해야 할 함정들이다.
> FE 페르소나 §8과 함께 적용한다.

### 8가지 실패 패턴과 Tailwind 대안

| AI 기본값 | 문제점 | 올바른 Tailwind 접근 |
|----------|--------|---------------------|
| Purple/indigo 도배 (`bg-purple-600`) | 모든 앱이 동일하게 보임 | **시맨틱 토큰 사용**: `bg-primary`, `text-accent` 등 CSS 변수 기반 |
| 과도한 그라디언트 (`bg-gradient-to-r from-purple-500 to-pink-500`) | 시각적 소음, shadcn 테마와 충돌 | **평면 우선**: 배경은 `bg-background`, 강조는 `bg-accent` |
| 모든 요소 `rounded-2xl` | 보더 반경 계층 무시, shadcn의 `--radius` 변수와 불일치 | **계층 적용**: 버튼 `rounded-md`, 카드 `rounded-lg`, 모달 `rounded-xl` |
| 제네릭 히어로 섹션 | 템플릿 주도, 콘텐츠 연결 없음 | **콘텐츠 우선**: 실제 데이터에 맞는 레이아웃 먼저 설계 |
| 로렘 입숨 (`Lorem ipsum dolor...`) | 실제 텍스트 길이·줄바꿈을 숨김 | **현실적 플레이스홀더**: 도메인에 맞는 예시 데이터 사용 |
| 과도한 패딩 (`p-8` everywhere) | 시각적 계층 파괴, 모바일에서 콘텐츠 영역 축소 | **스케일 기반**: `p-4`(기본), `p-6`(섹션), `p-8`(페이지 최상위만) |
| 주식형 카드 그리드 (동일 크기 카드 나열) | 정보 우선순위 무시 | **목적 기반**: 중요 콘텐츠는 더 큰 영역, 보조는 작게 |
| 그림자 과잉 (`shadow-xl`, `shadow-2xl`) | 렌더링 비용, shadcn의 미니멀 미학과 충돌 | **최소화**: 카드 `shadow-sm`, 모달 `shadow-lg`, 나머지는 없음 |

### 시맨틱 컬러 토큰 — 원색 직접 사용 금지

```
❌ text-purple-600     → ✅ text-primary
❌ bg-indigo-500       → ✅ bg-accent
❌ bg-gray-50          → ✅ bg-background
❌ text-gray-900       → ✅ text-foreground
❌ border-gray-200     → ✅ border-border
```

shadcn/ui의 CSS 변수(`--primary`, `--background` 등)를 Tailwind 유틸리티 클래스로 매핑해서 사용한다.
임의 색상(`bg-[#7c3aed]`)은 디자인 토큰이 확정되기 전 임시 용도로만 허용.

### 스페이싱 스케일 — 0.25rem 증분만 사용

```
❌ px-[13px]     ❌ py-[2.3rem]     ❌ gap-[22px]
✅ p-4 (1rem)    ✅ py-6 (1.5rem)   ✅ gap-2 (0.5rem)
```

임의 값(arbitrary value)은 Tailwind의 `[]` 문법으로 가능하지만 사용하지 않는다.
스케일을 벗어나는 간격이 필요하면 설계 재검토 신호다.

### AI Aesthetic 자가 점검

컴포넌트 PR 전에 확인:

- [ ] `bg-purple-*` / `bg-indigo-*` / `text-purple-*` 직접 사용 없음
- [ ] `bg-gradient-to-*` 2개 이상의 섹션에 사용 안 함
- [ ] `rounded-2xl`이 3가지 이상의 다른 요소 유형에 사용 안 함
- [ ] `shadow-xl` / `shadow-2xl` 카드에 사용 안 함
- [ ] Lorem ipsum 텍스트 없음
- [ ] `p-8` 이상이 작은 컨테이너(카드·모달 내부)에 사용 안 함
- [ ] `px-[*]` / `py-[*]` 같은 임의 픽셀값 없음

---

## 참조

- `personas/frontend.md` §8 — AI Aesthetic 회피 원칙
- `skills/templates/fe/styling_design.md` — 스타일링 설계 뷰 (AC용)
- `harness/skills/gate.md` — 게이트 검증 단계
- 원본: `agent-skills/skills/frontend-ui-engineering/SKILL.md` — Avoid the AI Aesthetic
