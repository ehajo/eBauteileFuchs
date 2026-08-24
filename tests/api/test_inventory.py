from decimal import Decimal

import pytest
from httpx import AsyncClient


async def _article(client: AsyncClient, name: str = "Synthetischer Widerstand") -> dict:
    categories = (await client.get("/api/v1/categories")).json()
    category = next(item for item in categories if item["code"] == "resistor")
    response = await client.post(
        "/api/v1/articles", json={"name": name, "category_id": category["id"]}
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _location(client: AsyncClient, code: str) -> dict:
    types = (await client.get("/api/v1/location-types")).json()
    drawer_type = next(item for item in types if item["code"] == "drawer")
    response = await client.post(
        "/api/v1/locations",
        json={
            "code": code,
            "name": f"Schublade {code}",
            "location_type_id": drawer_type["id"],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _headers(key: str) -> dict[str, str]:
    return {"Idempotency-Key": key}


@pytest.mark.anyio
async def test_initial_stock_in_out_total_and_idempotency(client: AsyncClient) -> None:
    article = await _article(client)
    first = await _location(client, "INV-01")
    second = await _location(client, "INV-02")
    payload = {
        "article_id": article["id"],
        "location_id": first["id"],
        "quantity": "10",
    }

    initial = await client.post(
        "/api/v1/inventory/initial", json=payload, headers=_headers("initial-0001")
    )
    assert initial.status_code == 201, initial.text
    assert Decimal(initial.json()["movements"][0]["balance_after"]) == 10

    repeated = await client.post(
        "/api/v1/inventory/initial", json=payload, headers=_headers("initial-0001")
    )
    assert repeated.status_code == 201
    assert repeated.json()["transaction_id"] == initial.json()["transaction_id"]
    assert repeated.json()["repeated"] is True

    second_initial = await client.post(
        "/api/v1/inventory/initial",
        json=payload,
        headers=_headers("initial-0002"),
    )
    assert second_initial.status_code == 409
    assert second_initial.json()["code"] == "inventory_conflict"

    changed_reuse = await client.post(
        "/api/v1/inventory/initial",
        json=payload | {"quantity": "11"},
        headers=_headers("initial-0001"),
    )
    assert changed_reuse.status_code == 409
    assert changed_reuse.json()["code"] == "idempotency_conflict"

    stock_in = await client.post(
        "/api/v1/inventory/stock-in",
        json=payload | {"location_id": second["id"], "quantity": "5.5"},
        headers=_headers("stock-in-0001"),
    )
    assert stock_in.status_code == 201
    stock_out = await client.post(
        "/api/v1/inventory/stock-out",
        json=payload | {"quantity": "3"},
        headers=_headers("stock-out-0001"),
    )
    assert stock_out.status_code == 201
    assert Decimal(stock_out.json()["movements"][0]["balance_after"]) == 7

    positions = await client.get(
        "/api/v1/inventory", params={"article_id": article["id"]}
    )
    assert positions.status_code == 200
    assert sum(Decimal(item["quantity"]) for item in positions.json()) == Decimal(
        "12.5"
    )
    journal = await client.get(
        "/api/v1/inventory/transactions", params={"article_id": article["id"]}
    )
    assert len(journal.json()) == 3


@pytest.mark.anyio
async def test_full_stock_out_and_negative_stock_are_atomic(
    client: AsyncClient,
) -> None:
    article = await _article(client, "Synthetischer Kondensator")
    location = await _location(client, "INV-03")
    payload = {
        "article_id": article["id"],
        "location_id": location["id"],
        "quantity": "5",
    }
    assert (
        await client.post(
            "/api/v1/inventory/stock-in",
            json=payload,
            headers=_headers("stock-in-0002"),
        )
    ).status_code == 201

    rejected = await client.post(
        "/api/v1/inventory/stock-out",
        json=payload | {"quantity": "6"},
        headers=_headers("stock-out-0002"),
    )
    assert rejected.status_code == 409
    assert rejected.json()["available"] == "5"
    positions = (await client.get("/api/v1/inventory")).json()
    assert Decimal(positions[0]["quantity"]) == 5

    all_out = await client.post(
        "/api/v1/inventory/stock-out", json=payload, headers=_headers("stock-out-0003")
    )
    assert all_out.status_code == 201
    assert Decimal(all_out.json()["movements"][0]["balance_after"]) == 0
    assert (await client.get("/api/v1/inventory")).json() == []
    with_zero = await client.get("/api/v1/inventory", params={"include_zero": True})
    assert Decimal(with_zero.json()[0]["quantity"]) == 0


@pytest.mark.anyio
async def test_transfer_and_failed_transfer_have_no_partial_booking(
    client: AsyncClient,
) -> None:
    article = await _article(client, "Synthetische Diode")
    source = await _location(client, "INV-04")
    target = await _location(client, "INV-05")
    base = {"article_id": article["id"], "location_id": source["id"], "quantity": "8"}
    await client.post(
        "/api/v1/inventory/stock-in", json=base, headers=_headers("stock-in-0003")
    )
    transfer = {
        "article_id": article["id"],
        "source_location_id": source["id"],
        "target_location_id": target["id"],
        "quantity": "3",
    }
    moved = await client.post(
        "/api/v1/inventory/transfers", json=transfer, headers=_headers("transfer-0001")
    )
    assert moved.status_code == 201, moved.text
    assert len(moved.json()["movements"]) == 2
    assert {item["transaction_id"] for item in moved.json()["movements"]} == {
        moved.json()["transaction_id"]
    }
    assert {Decimal(item["balance_after"]) for item in moved.json()["movements"]} == {
        3,
        5,
    }

    failed = await client.post(
        "/api/v1/inventory/transfers",
        json=transfer | {"quantity": "9"},
        headers=_headers("transfer-0002"),
    )
    assert failed.status_code == 409
    positions = (await client.get("/api/v1/inventory")).json()
    assert sorted(Decimal(item["quantity"]) for item in positions) == [3, 5]
    journal = (await client.get("/api/v1/inventory/transactions")).json()
    assert len(journal) == 3


@pytest.mark.anyio
async def test_positive_negative_and_target_adjustments(client: AsyncClient) -> None:
    article = await _article(client, "Synthetischer IC")
    location = await _location(client, "INV-06")
    common = {"article_id": article["id"], "location_id": location["id"]}
    positive = await client.post(
        "/api/v1/inventory/adjustments",
        json=common | {"difference": "5", "comment": "Inventur"},
        headers=_headers("adjustment-0001"),
    )
    assert Decimal(positive.json()["movements"][0]["balance_after"]) == 5
    negative = await client.post(
        "/api/v1/inventory/adjustments",
        json=common | {"difference": "-2"},
        headers=_headers("adjustment-0002"),
    )
    assert Decimal(negative.json()["movements"][0]["balance_after"]) == 3
    target = await client.post(
        "/api/v1/inventory/adjustments",
        json=common | {"target_quantity": "7"},
        headers=_headers("adjustment-0003"),
    )
    assert Decimal(target.json()["movements"][0]["quantity_delta"]) == 4
    assert Decimal(target.json()["movements"][0]["balance_after"]) == 7


@pytest.mark.anyio
async def test_invalid_and_inactive_locations_are_rejected(client: AsyncClient) -> None:
    article = await _article(client, "Synthetisches mechanisches Teil")
    location = await _location(client, "INV-07")
    await client.delete(f"/api/v1/locations/{location['id']}")
    response = await client.post(
        "/api/v1/inventory/stock-in",
        json={
            "article_id": article["id"],
            "location_id": location["id"],
            "quantity": "1",
        },
        headers=_headers("stock-in-0004"),
    )
    assert response.status_code == 409
    assert response.json()["code"] == "inactive_location"

    invalid = await client.post(
        "/api/v1/inventory/stock-in",
        json={
            "article_id": article["id"],
            "location_id": location["id"],
            "quantity": "0",
        },
        headers=_headers("stock-in-0005"),
    )
    assert invalid.status_code == 422
