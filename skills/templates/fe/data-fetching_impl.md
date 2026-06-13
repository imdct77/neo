# 데이터 패칭 — 구현 뷰 (FE용)

> **로드 시점**: Phase 3 Task Brief 작성 시 (FE 구현)
> **설계 구조**: `data-fetching_design.md` 참조
> **스택**: Next.js 14+ / TanStack Query v5

---

## API 클라이언트 — Server 전용 (lib/api/server.ts)

```typescript
// Server Component 전용. "use client" 파일에서 import 금지.
const BASE_URL = process.env.API_BASE_URL; // 서버 환경변수 (NEXT_PUBLIC_ 불필요)

interface FetchOptions extends RequestInit {
  tags?: string[];
  revalidate?: number | false;
}

export async function serverFetch<T>(
  path: string,
  options: FetchOptions = {}
): Promise<T> {
  const { tags, revalidate, ...fetchOptions } = options;

  const res = await fetch(`${BASE_URL}${path}`, {
    ...fetchOptions,
    next: {
      ...(tags && { tags }),
      ...(revalidate !== undefined && { revalidate }),
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.message ?? `API 오류: ${res.status}`);
  }

  return res.json();
}
```

---

## API 클라이언트 — Client 전용 (lib/api/client.ts)

```typescript
"use client";

import { useAuthStore } from "@/stores/useAuthStore";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

export async function clientFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = useAuthStore.getState().accessToken;

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
  });

  if (res.status === 401) {
    useAuthStore.getState().clearAuth();
    window.location.href = "/login";
    throw new Error("인증이 만료됐습니다.");
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.message ?? `API 오류: ${res.status}`);
  }

  return res.json();
}
```

---

## 도메인 API 함수 (lib/api/orders.ts)

```typescript
import { serverFetch } from "./server";
import { clientFetch } from "./client";
import type { Order, CreateOrderRequest } from "@/types/order";

// Server Component용
export async function getOrders(filters?: { status?: string }): Promise<Order[]> {
  const params = new URLSearchParams(filters as Record<string, string>);
  return serverFetch<Order[]>(`/api/v1/orders?${params}`, {
    revalidate: false,  // 사용자별 데이터 — 캐시 없음
  });
}

// Client Component용 (TanStack Query에서 호출)
export async function fetchOrders(filters?: { status?: string }): Promise<Order[]> {
  const params = new URLSearchParams(
    Object.entries(filters ?? {}).filter(([, v]) => v !== undefined) as [string, string][]
  );
  return clientFetch<Order[]>(`/api/v1/orders?${params}`);
}

export async function createOrder(data: CreateOrderRequest): Promise<Order> {
  return clientFetch<Order>("/api/v1/orders", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
```

---

## Server Component 패칭 패턴

```tsx
// app/(dashboard)/orders/page.tsx
import { getOrders } from "@/lib/api/orders";
import { OrderList } from "@/components/order/OrderList";
import { notFound } from "next/navigation";

export default async function OrdersPage() {
  let orders;
  try {
    orders = await getOrders();
  } catch (error) {
    // 404는 notFound()로, 나머지는 error.tsx로 전파
    if (error instanceof Error && error.message.includes("404")) {
      notFound();
    }
    throw error;  // error.tsx가 처리
  }

  return <OrderList orders={orders} />;
}
```

---

## Server Action 패턴 (폼 제출)

```typescript
// app/(dashboard)/orders/actions.ts
"use server";

import { revalidateTag } from "next/cache";
import { serverFetch } from "@/lib/api/server";
import type { CreateOrderRequest } from "@/types/order";

export async function createOrderAction(data: CreateOrderRequest) {
  try {
    await serverFetch("/api/v1/orders", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
    revalidateTag("orders");  // 캐시 무효화
    return { success: true };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "오류가 발생했습니다.",
    };
  }
}
```
