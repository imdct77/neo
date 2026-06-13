# 상태 관리 — 구현 뷰 (FE용)

> **로드 시점**: Phase 3 Task Brief 작성 시 (FE 구현)
> **설계 구조**: `state-management_design.md` 참조
> **스택**: Next.js 14+ / TanStack Query v5 / Zustand v4

---

## TanStack Query 설정 (lib/query-client.ts)

```typescript
import { QueryClient } from "@tanstack/react-query";

export function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000,   // 5분
        retry: 1,
        refetchOnWindowFocus: false,
      },
      mutations: {
        onError: (error) => {
          console.error("[Query Mutation Error]", error);
        },
      },
    },
  });
}
```

```tsx
// app/providers.tsx
"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { useState } from "react";
import { makeQueryClient } from "@/lib/query-client";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(makeQueryClient);

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

---

## 도메인 쿼리 훅 패턴 (hooks/useOrders.ts)

```typescript
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchOrders, createOrder, updateOrder } from "@/lib/api/orders";
import type { CreateOrderRequest, Order } from "@/types/order";

// 캐시 키 상수 — 파일 최상단에 정의
export const orderKeys = {
  all: ["orders"] as const,
  lists: () => [...orderKeys.all, "list"] as const,
  list: (filters: Record<string, unknown>) => [...orderKeys.lists(), filters] as const,
  detail: (id: number) => [...orderKeys.all, "detail", id] as const,
};


export function useOrders(filters?: { status?: string }) {
  return useQuery({
    queryKey: orderKeys.list(filters ?? {}),
    queryFn: () => fetchOrders(filters),
  });
}

export function useOrder(id: number) {
  return useQuery({
    queryKey: orderKeys.detail(id),
    queryFn: () => fetchOrders({ id }),
    enabled: !!id,  // id가 없으면 실행하지 않음
  });
}

export function useCreateOrder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateOrderRequest) => createOrder(data),
    onSuccess: () => {
      // 성공 시 목록 전체 무효화
      queryClient.invalidateQueries({ queryKey: orderKeys.lists() });
    },
  });
}
```

---

## Zustand 스토어 패턴 (stores/useAuthStore.ts)

```typescript
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { User } from "@/types/user";

interface AuthState {
  user: User | null;
  accessToken: string | null;

  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,

      setAuth: (user, accessToken) => set({ user, accessToken }),
      clearAuth: () => set({ user: null, accessToken: null }),
      isAuthenticated: () => get().accessToken !== null,
    }),
    {
      name: "auth-storage",
      storage: createJSONStorage(() => sessionStorage),
      // accessToken만 저장. 민감 정보 최소화
      partialize: (state) => ({
        accessToken: state.accessToken,
        user: state.user,
      }),
    }
  )
);
```

```typescript
// stores/useUIStore.ts — UI 전역 상태 (persist 불필요)
import { create } from "zustand";

interface UIState {
  isSidebarOpen: boolean;
  toggleSidebar: () => void;

  activeModal: string | null;
  openModal: (modalId: string) => void;
  closeModal: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  isSidebarOpen: true,
  toggleSidebar: () => set((s) => ({ isSidebarOpen: !s.isSidebarOpen })),

  activeModal: null,
  openModal: (modalId) => set({ activeModal: modalId }),
  closeModal: () => set({ activeModal: null }),
}));
```

---

## 컴포넌트에서 조합 패턴

```tsx
// components/order/OrderListClient.tsx
"use client";

import { useOrders, useCreateOrder } from "@/hooks/useOrders";
import { useUIStore } from "@/stores/useUIStore";
import { AppButton } from "@/components/common/AppButton";
import { OrderCard } from "./OrderCard";
import { Skeleton } from "@/components/ui/skeleton";

export function OrderListClient() {
  const { data: orders, isLoading, error } = useOrders();
  const createOrder = useCreateOrder();
  const openModal = useUIStore((s) => s.openModal);

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-24 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        데이터를 불러올 수 없습니다.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <AppButton onClick={() => openModal("create-order")}>
          주문 생성
        </AppButton>
      </div>
      {orders?.items.map((order) => (
        <OrderCard key={order.id} order={order} />
      ))}
    </div>
  );
}
```
