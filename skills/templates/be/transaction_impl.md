# 트랜잭션 관리 — 구현 뷰 (BE용)

> **로드 시점**: Phase 3 Task Brief 작성 시 (BE 구현)
> **설계 구조**: `transaction_design.md` 참조
> **스택**: Python / FastAPI / SQLAlchemy 2.x (async)

---

## 기본 패턴 — 세션 자동 관리

단일 테이블 CRUD는 `get_session`의 yield 패턴이 트랜잭션을 자동 관리한다.
별도 트랜잭션 코드를 작성하지 않아도 된다.

```python
# core/database.py의 get_session이 이미 처리함
async def get_session() -> AsyncSession:
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()   # 요청 정상 종료 시 자동 커밋
        except Exception:
            await session.rollback() # 예외 발생 시 자동 롤백
            raise
```

---

## 명시적 트랜잭션 — 멀티 Repository 작업

여러 Repository 작업을 하나의 트랜잭션으로 묶어야 할 때:

```python
# order/service.py
class OrderService:
    def __init__(
        self,
        order_repo: OrderRepository,
        inventory_repo: InventoryRepository,
        session: AsyncSession,  # 트랜잭션 제어용 세션 직접 주입
    ) -> None:
        self._order_repo = order_repo
        self._inventory_repo = inventory_repo
        self._session = session

    async def create_order(self, user_id: int, items: list[OrderItemRequest]) -> OrderDTO:
        # 재고 확인 (읽기 — 트랜잭션 시작 전)
        for item in items:
            stock = await self._inventory_repo.get_stock(item.product_id)
            if stock < item.quantity:
                raise InsufficientStockError(item.product_id)

        # 트랜잭션 내 작업
        async with self._session.begin_nested():  # Savepoint
            order = await self._order_repo.create(user_id=user_id)
            for item in items:
                await self._order_repo.add_item(order.id, item)
                await self._inventory_repo.decrement(item.product_id, item.quantity)

        # session.commit()은 get_session이 처리 — 여기서 호출하지 않음
        return order
```

---

## Savepoint 패턴 — 부분 롤백

전체 트랜잭션을 롤백하지 않고 특정 작업만 롤백할 때:

```python
async def process_with_fallback(self, data: ProcessRequest) -> ResultDTO:
    try:
        async with self._session.begin_nested():  # Savepoint 생성
            result = await self._repo.risky_operation(data)
            return result
    except SpecificDomainError:
        # Savepoint까지만 롤백. 상위 트랜잭션은 유지됨
        fallback = await self._repo.safe_fallback(data)
        return fallback
```

---

## 외부 API 호출 패턴 — 트랜잭션 경계 밖

```python
async def create_order_with_payment(
    self, user_id: int, payment_info: PaymentRequest
) -> OrderDTO:
    # 1. DB 작업 먼저 (트랜잭션 안)
    order = await self._order_repo.create_pending(user_id)

    # 2. 외부 API는 트랜잭션 밖에서 호출
    #    (get_session의 commit은 요청 종료 시 실행되므로
    #     여기서 flush로 ID만 확보하고 commit은 나중에)
    await self._session.flush()

    # 3. 외부 결제 API 호출
    payment_result = await self._payment_client.charge(
        order_id=order.id,
        amount=payment_info.amount,
    )

    if not payment_result.success:
        # 결제 실패 시 주문 취소 처리 (DB 롤백이 아닌 비즈니스 취소)
        await self._order_repo.cancel(order.id)
        raise PaymentFailedError(payment_result.error_code)

    # 4. 결제 성공 후 상태 업데이트
    return await self._order_repo.confirm(order.id, payment_result.transaction_id)
```

---

## 배치 작업 — 청크 단위 트랜잭션

```python
async def bulk_process(self, items: list[ItemDTO]) -> BulkResult:
    CHUNK_SIZE = 100
    success_count = 0
    failed_ids = []

    for i in range(0, len(items), CHUNK_SIZE):
        chunk = items[i:i + CHUNK_SIZE]
        try:
            async with self._session.begin_nested():  # 청크 단위 Savepoint
                for item in chunk:
                    await self._repo.process(item)
                success_count += len(chunk)
        except Exception as e:
            # 이 청크만 롤백. 다음 청크 계속 진행
            failed_ids.extend([item.id for item in chunk])

    return BulkResult(success=success_count, failed=failed_ids)
```
