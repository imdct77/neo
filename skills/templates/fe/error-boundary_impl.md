# 에러 바운더리 — 구현 뷰 (FE용)

> **로드 시점**: Phase 3 Task Brief 작성 시 (FE 구현)
> **설계 구조**: `error-boundary_design.md` 참조
> **스택**: Next.js 14+ / React

---

## 전역 에러 경계 (app/error.tsx)

```tsx
"use client";

import { useEffect } from "react";
import { AppButton } from "@/components/common/AppButton";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function GlobalError({ error, reset }: ErrorProps) {
  useEffect(() => {
    // 에러 로깅 서비스 연동 지점
    console.error("[Global Error]", error);
  }, [error]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4">
      <h2 className="text-xl font-semibold">문제가 발생했습니다</h2>
      <p className="text-muted-foreground text-sm">
        잠시 후 다시 시도해주세요.
      </p>
      <AppButton onClick={reset}>다시 시도</AppButton>
    </div>
  );
}
```

---

## 페이지 레벨 에러 경계 (app/{route}/error.tsx)

```tsx
"use client";

import { AppButton } from "@/components/common/AppButton";

export default function OrdersError({
  error,
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-4">
      <p className="text-muted-foreground">주문 목록을 불러올 수 없습니다.</p>
      <AppButton variant="outline" onClick={reset}>
        다시 시도
      </AppButton>
    </div>
  );
}
```

---

## 로딩 상태 (app/{route}/loading.tsx)

```tsx
import { Skeleton } from "@/components/ui/skeleton";

export default function OrdersLoading() {
  return (
    <div className="container mx-auto py-8 space-y-4">
      <Skeleton className="h-8 w-48" />
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-24 w-full rounded-lg" />
      ))}
    </div>
  );
}
```

---

## Not Found (app/not-found.tsx)

```tsx
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4">
      <h2 className="text-2xl font-bold">페이지를 찾을 수 없습니다</h2>
      <p className="text-muted-foreground">요청하신 페이지가 존재하지 않습니다.</p>
      <Button asChild>
        <Link href="/">홈으로 돌아가기</Link>
      </Button>
    </div>
  );
}
```

---

## 컴포넌트 레벨 ErrorBoundary (react-error-boundary 사용)

```tsx
// components/common/SectionErrorBoundary.tsx
"use client";

import { ErrorBoundary } from "react-error-boundary";
import { AppButton } from "./AppButton";

function SectionFallback({
  error,
  resetErrorBoundary,
}: {
  error: Error;
  resetErrorBoundary: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center p-8 border border-dashed rounded-lg gap-3">
      <p className="text-sm text-muted-foreground">
        이 섹션을 불러올 수 없습니다.
      </p>
      <AppButton variant="ghost" size="sm" onClick={resetErrorBoundary}>
        재시도
      </AppButton>
    </div>
  );
}

export function SectionErrorBoundary({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ErrorBoundary FallbackComponent={SectionFallback}>
      {children}
    </ErrorBoundary>
  );
}
```
