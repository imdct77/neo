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
