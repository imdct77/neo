# 폼 처리 — 구현 뷰 (FE용)

> **로드 시점**: Phase 3 Task Brief 작성 시 (FE 구현)
> **설계 구조**: `form-handling_design.md` 참조
> **스택**: Next.js 14+ / react-hook-form / zod / shadcn/ui

---

## zod 스키마 정의 (lib/schemas/order.ts)

```typescript
import { z } from "zod";

export const createOrderSchema = z.object({
  productId: z.number({ required_error: "상품을 선택해주세요." }),
  quantity: z
    .number({ required_error: "수량을 입력해주세요." })
    .min(1, "수량은 1 이상이어야 합니다.")
    .max(100, "수량은 100을 초과할 수 없습니다."),
  deliveryAddress: z
    .string({ required_error: "배송지를 입력해주세요." })
    .min(5, "배송지를 정확히 입력해주세요."),
  notes: z.string().max(200, "메모는 200자 이하로 입력해주세요.").optional(),
});

export type CreateOrderFormData = z.infer<typeof createOrderSchema>;
```

---

## 폼 컴포넌트 패턴 (components/order/CreateOrderForm.tsx)

```tsx
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Form, FormControl, FormField, FormItem, FormLabel, FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { AppButton } from "@/components/common/AppButton";
import { useCreateOrder } from "@/hooks/useOrders";
import { createOrderSchema, type CreateOrderFormData } from "@/lib/schemas/order";
import { useToast } from "@/hooks/use-toast";

interface CreateOrderFormProps {
  onSuccess?: () => void;
}

export function CreateOrderForm({ onSuccess }: CreateOrderFormProps) {
  const { toast } = useToast();
  const createOrder = useCreateOrder();

  const form = useForm<CreateOrderFormData>({
    resolver: zodResolver(createOrderSchema),
    defaultValues: {
      productId: undefined,
      quantity: 1,
      deliveryAddress: "",
      notes: "",
    },
  });

  async function onSubmit(data: CreateOrderFormData) {
    try {
      await createOrder.mutateAsync(data);
      toast({ title: "주문이 생성됐습니다." });
      form.reset();
      onSuccess?.();
    } catch (error) {
      // 서버 에러를 폼 필드 에러로 매핑
      if (error instanceof Error) {
        if (error.message.includes("PRODUCT_NOT_FOUND")) {
          form.setError("productId", { message: "존재하지 않는 상품입니다." });
        } else {
          form.setError("root", { message: error.message });
        }
      }
    }
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">

        <FormField
          control={form.control}
          name="quantity"
          render={({ field }) => (
            <FormItem>
              <FormLabel>수량</FormLabel>
              <FormControl>
                <Input
                  type="number"
                  {...field}
                  onChange={(e) => field.onChange(Number(e.target.value))}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="deliveryAddress"
          render={({ field }) => (
            <FormItem>
              <FormLabel>배송지</FormLabel>
              <FormControl>
                <Input placeholder="배송 받을 주소를 입력하세요" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="notes"
          render={({ field }) => (
            <FormItem>
              <FormLabel>메모 (선택)</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="배송 관련 요청사항을 입력하세요"
                  className="resize-none"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* 루트 에러 (서버 에러) 표시 */}
        {form.formState.errors.root && (
          <p className="text-sm text-destructive">
            {form.formState.errors.root.message}
          </p>
        )}

        <AppButton
          type="submit"
          className="w-full"
          isLoading={createOrder.isPending}
        >
          주문하기
        </AppButton>

      </form>
    </Form>
  );
}
```

---

## Server Action 폼 패턴

```tsx
// components/order/CreateOrderFormServer.tsx
"use client";

import { useFormState, useFormStatus } from "react-dom";
import { createOrderAction } from "@/app/(dashboard)/orders/actions";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <Button type="submit" disabled={pending}>
      {pending ? "처리 중..." : "주문하기"}
    </Button>
  );
}

export function CreateOrderFormServer() {
  const [state, formAction] = useFormState(createOrderAction, null);

  return (
    <form action={formAction} className="space-y-4">
      <Input name="deliveryAddress" placeholder="배송지" required />
      {state?.error && (
        <p className="text-sm text-destructive">{state.error}</p>
      )}
      <SubmitButton />
    </form>
  );
}
```
