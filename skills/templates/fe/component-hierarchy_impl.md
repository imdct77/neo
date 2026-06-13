# 컴포넌트 계층 — 구현 뷰 (FE용)

> **로드 시점**: Phase 3 Task Brief 작성 시 (FE 구현)
> **설계 구조**: `component-hierarchy_design.md` 참조
> **스택**: Next.js 14+ / React / TypeScript / shadcn/ui / Tailwind

---

## Server Component — 데이터 패칭 패턴

```tsx
// app/(dashboard)/orders/page.tsx
import { OrderList } from "@/components/order/OrderList";
import { getOrders } from "@/lib/api/orders";

// Server Component: async 함수로 직접 데이터 패칭
export default async function OrdersPage() {
  const orders = await getOrders();

  return (
    <main className="container mx-auto py-8">
      <h1 className="text-2xl font-bold mb-6">주문 목록</h1>
      <OrderList orders={orders} />
    </main>
  );
}
```

---

## Client Component — 최소 범위 원칙

```tsx
// components/order/OrderList.tsx
// Server Component: 목록 렌더링
import { OrderCard } from "./OrderCard";
import { OrderFilterClient } from "./OrderFilterClient";
import type { Order } from "@/types/order";

interface OrderListProps {
  orders: Order[];
}

export function OrderList({ orders }: OrderListProps) {
  return (
    <div>
      {/* 상호작용이 필요한 부분만 Client Component로 분리 */}
      <OrderFilterClient />
      <ul className="space-y-4">
        {orders.map((order) => (
          <OrderCard key={order.id} order={order} />
        ))}
      </ul>
    </div>
  );
}
```

```tsx
// components/order/OrderFilterClient.tsx
"use client"; // Client Component는 파일 최상단에 선언

import { useState } from "react";
import { Button } from "@/components/ui/button";

type FilterStatus = "all" | "pending" | "completed";

export function OrderFilterClient() {
  const [status, setStatus] = useState<FilterStatus>("all");

  return (
    <div className="flex gap-2 mb-4">
      {(["all", "pending", "completed"] as FilterStatus[]).map((s) => (
        <Button
          key={s}
          variant={status === s ? "default" : "outline"}
          size="sm"
          onClick={() => setStatus(s)}
        >
          {s}
        </Button>
      ))}
    </div>
  );
}
```

---

## shadcn/ui 컴포넌트 확장 패턴

shadcn 원본(`components/ui/`)을 수정하지 않는다.
`components/common/` 또는 `components/{domain}/`에서 래핑한다.

```tsx
// components/common/AppButton.tsx
import { Button, type ButtonProps } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface AppButtonProps extends ButtonProps {
  isLoading?: boolean;
}

export function AppButton({ isLoading, children, className, disabled, ...props }: AppButtonProps) {
  return (
    <Button
      className={cn("min-w-[80px]", className)}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <>
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          처리 중...
        </>
      ) : (
        children
      )}
    </Button>
  );
}
```

---

## 공통 레이아웃 패턴

```tsx
// components/common/PageLayout.tsx
import { cn } from "@/lib/utils";

interface PageLayoutProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export function PageLayout({
  title, description, actions, children, className,
}: PageLayoutProps) {
  return (
    <div className={cn("container mx-auto py-8 space-y-6", className)}>
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
          {description && (
            <p className="text-muted-foreground mt-1">{description}</p>
          )}
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>
      {children}
    </div>
  );
}
```

---

## 타입 정의 패턴 (types/order.ts)

```typescript
// API 응답 타입 (BE schema와 1:1 대응)
export interface Order {
  id: number;
  userId: number;
  status: OrderStatus;
  totalAmount: number;
  createdAt: string;
}

export type OrderStatus = "pending" | "confirmed" | "shipped" | "delivered" | "cancelled";

// 컴포넌트 Props 타입은 컴포넌트 파일 안에 정의
// 여러 컴포넌트가 공유하는 타입만 types/ 에 정의
```
