import importlib

import pytest
from httpx import AsyncClient

from ebauteilefuchs.platform.network import NetworkAddress


@pytest.mark.anyio
async def test_global_and_search_uses_supplier_attributes_notes_and_location_paths(
    client: AsyncClient,
) -> None:
    categories = (await client.get("/api/v1/categories")).json()
    category = next(item for item in categories if item["code"] == "resistor")
    attributes = (
        await client.get(f"/api/v1/categories/{category['id']}/attributes")
    ).json()
    resistance = next(item for item in attributes if item["code"] == "resistance")
    supplier = (await client.get("/api/v1/suppliers")).json()[0]
    article = (
        await client.post(
            "/api/v1/articles",
            json={
                "name": "Synthetischer Präzisionswiderstand",
                "category_id": category["id"],
                "manufacturer_name": "Synthetic Parts",
                "manufacturer_part_number": "SP-10K-0805",
                "note": "Nur für Reparaturen",
                "attributes": [
                    {
                        "definition_id": resistance["id"],
                        "raw_value": "10 kΩ",
                        "unit": "Ω",
                    },
                    {"custom_name": "Lagerhinweis", "raw_value": "trocken"},
                ],
                "supplier_parts": [
                    {
                        "supplier_id": supplier["id"],
                        "supplier_part_number": "71-SYNTH-10K",
                    }
                ],
            },
        )
    ).json()
    types = (await client.get("/api/v1/location-types")).json()

    async def location(code: str, type_code: str, parent_id: str | None = None):
        location_type = next(item for item in types if item["code"] == type_code)
        response = await client.post(
            "/api/v1/locations",
            json={
                "code": code,
                "name": code,
                "location_type_id": location_type["id"],
                "parent_id": parent_id,
            },
        )
        return response.json()

    room = await location("LABOR", "room")
    shelf = await location("REGAL-A", "shelf", room["id"])
    box = await location("BOX-07", "box", shelf["id"])
    booked = await client.post(
        "/api/v1/inventory/stock-in",
        headers={"Idempotency-Key": "m5-search-stock-1"},
        json={"article_id": article["id"], "location_id": box["id"], "quantity": "4"},
    )
    assert booked.status_code == 201

    for query in (
        "10k trocken",
        "10kΩ trocken",
        "reparaturen REGAL-A",
        "71-SYNTH-10K BOX-07",
        "Synthetic 0805",
    ):
        response = await client.get("/api/v1/search", params={"q": query})
        assert response.status_code == 200, response.text
        assert [item["article_id"] for item in response.json()["items"]] == [
            article["id"]
        ]

    filtered = await client.get(
        "/api/v1/search",
        params={
            "q": "10k",
            "category_id": category["id"],
            "with_stock": True,
            "location_scope_id": room["id"],
        },
    )
    assert filtered.status_code == 200
    assert filtered.json()["items"][0]["positions"][0]["path"].endswith("BOX-07")

    page = await client.get("/search", params={"q": "10k REGAL-A"})
    assert page.status_code == 200
    assert "Synthetischer Präzisionswiderstand" in page.text
    assert 'id="global-query"' in page.text
    assert "autofocus" in page.text


@pytest.mark.anyio
async def test_connection_api_qr_and_manual_url_validation(
    client: AsyncClient, monkeypatch
) -> None:
    route_module = importlib.import_module("ebauteilefuchs.api.v1.search")
    monkeypatch.setattr(
        route_module,
        "discover_ipv4_addresses",
        lambda: (NetworkAddress("192.168.10.42", True),),
    )
    monkeypatch.setattr(route_module, "hostname", lambda: "synthetic-pc")
    status = await client.get("/api/v1/connection")
    assert status.status_code == 200
    assert status.json()["hostname"] == "synthetic-pc"
    assert status.json()["selected_url"] == "http://192.168.10.42:8008"

    qr = await client.get(
        "/connection/qr.svg", params={"base_url": "http://192.168.10.42:8008"}
    )
    assert qr.status_code == 200
    assert qr.headers["content-type"].startswith("image/svg+xml")
    assert b"<svg" in qr.content

    rejected = await client.get(
        "/connection/qr.svg", params={"base_url": "javascript:alert(1)"}
    )
    assert rejected.status_code == 422
    page = await client.get(
        "/connection", params={"base_url": "http://192.168.10.42:8008/path"}
    )
    assert page.status_code == 200
    assert "keinen Pfad" in page.text
