from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError

from ebauteilefuchs.application.inventory import InventoryService
from ebauteilefuchs.config import Settings
from ebauteilefuchs.domain.errors import InsufficientStockError
from ebauteilefuchs.persistence.database import (
    create_database_engine,
    create_session_factory,
)
from ebauteilefuchs.persistence.inventory import SqlAlchemyInventoryUnitOfWork
from ebauteilefuchs.persistence.models import (
    InventoryBalanceModel,
    InventoryMovementModel,
)


async def _references(client: AsyncClient) -> tuple[str, str]:
    category = next(
        item
        for item in (await client.get("/api/v1/categories")).json()
        if item["code"] == "other"
    )
    article = await client.post(
        "/api/v1/articles",
        json={"name": "Synthetischer Paralleltest", "category_id": category["id"]},
    )
    location_type = next(
        item
        for item in (await client.get("/api/v1/location-types")).json()
        if item["code"] == "drawer"
    )
    location = await client.post(
        "/api/v1/locations",
        json={
            "code": "PAR-01",
            "name": "Parallelschublade",
            "location_type_id": location_type["id"],
        },
    )
    return article.json()["id"], location.json()["id"]


@pytest.mark.anyio
async def test_concurrent_stock_out_never_creates_negative_balance_and_journal_is_immutable(
    client: AsyncClient, test_settings: Settings
) -> None:
    article_id, location_id = await _references(client)
    initial = await client.post(
        "/api/v1/inventory/initial",
        json={"article_id": article_id, "location_id": location_id, "quantity": "5"},
        headers={"Idempotency-Key": "parallel-initial-0001"},
    )
    assert initial.status_code == 201

    engine = create_database_engine(test_settings)
    factory = create_session_factory(engine)
    barrier = Barrier(2)

    def withdraw(key: str) -> str:
        service = InventoryService(lambda: SqlAlchemyInventoryUnitOfWork(factory))
        barrier.wait()
        try:
            service.stock_out(
                article_id=article_id,
                location_id=location_id,
                quantity="4",
                idempotency_key=key,
            )
        except InsufficientStockError:
            return "rejected"
        return "booked"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(
            executor.map(withdraw, ("parallel-out-0001", "parallel-out-0002"))
        )
    assert sorted(results) == ["booked", "rejected"]

    with factory() as session:
        balance = session.scalar(select(InventoryBalanceModel))
        assert balance is not None
        assert balance.quantity == Decimal("1.00000000")
        journal_sum = session.scalar(
            select(func.sum(InventoryMovementModel.quantity_delta))
        )
        assert journal_sum == balance.quantity
        assert session.scalar(select(func.count(InventoryMovementModel.id))) == 2

    with pytest.raises(DBAPIError), engine.begin() as connection:
        connection.execute(text("UPDATE inventory_movement SET quantity_delta = 99"))
    with pytest.raises(DBAPIError), engine.begin() as connection:
        connection.execute(text("DELETE FROM inventory_transaction"))
    engine.dispose()
