import json
from pathlib import Path

import pytest
from httpx import AsyncClient

from ebauteilefuchs.domain.errors import (
    SupplierAuthenticationError,
    SupplierRateLimitError,
    SupplierUnavailableError,
)
from ebauteilefuchs.domain.suppliers import SupplierSearchMode
from ebauteilefuchs.suppliers.mouser.mapper import map_part
from ebauteilefuchs.suppliers.mouser.schemas import parse_search_response

FIXTURES = Path(__file__).parents[1] / "fixtures" / "mouser"


class FakeAdapter:
    code = "mouser"
    configured = True

    def __init__(self, products=(), error=None) -> None:
        self.products = tuple(products)
        self.error = error
        self.calls = 0

    def search(self, query: str, mode: SupplierSearchMode):
        self.calls += 1
        if self.error:
            raise self.error
        return self.products


def products(name: str):
    payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return tuple(map_part(item) for item in parse_search_response(payload))


def set_adapter(client: AsyncClient, adapter: FakeAdapter) -> None:
    client._transport.app.state.supplier_adapter = adapter


@pytest.mark.anyio
async def test_missing_key_and_supplier_error_statuses(client: AsyncClient) -> None:
    missing = await client.post(
        "/api/v1/suppliers/mouser/search",
        json={"query": "unknown", "mode": "keyword"},
    )
    assert missing.status_code == 503
    assert "nicht eingerichtet" in missing.json()["detail"]

    for error, expected in (
        (SupplierAuthenticationError("Schlüssel abgelehnt."), 502),
        (SupplierRateLimitError("Limit erreicht."), 429),
        (SupplierUnavailableError("Netzwerk nicht erreichbar."), 503),
    ):
        set_adapter(client, FakeAdapter(error=error))
        response = await client.post(
            "/api/v1/suppliers/mouser/search",
            json={"query": "external-only", "mode": "keyword"},
        )
        assert response.status_code == expected


@pytest.mark.anyio
async def test_local_match_prevents_unrequested_external_search(
    client: AsyncClient,
) -> None:
    category = next(
        item
        for item in (await client.get("/api/v1/categories")).json()
        if item["code"] == "other"
    )
    supplier = (await client.get("/api/v1/suppliers")).json()[0]
    created = await client.post(
        "/api/v1/articles",
        json={
            "name": "Lokal bekannter Scanartikel",
            "category_id": category["id"],
            "supplier_parts": [
                {"supplier_id": supplier["id"], "supplier_part_number": "LOCAL-4711"}
            ],
        },
    )
    fake = FakeAdapter(products("search_one.json"))
    set_adapter(client, fake)
    found = await client.post(
        "/api/v1/suppliers/mouser/search",
        json={"query": "LOCAL-4711", "mode": "barcode"},
    )
    assert found.status_code == 200
    assert found.json()["local_matches"][0]["id"] == created.json()["id"]
    assert found.json()["external_searched"] is False
    assert fake.calls == 0

    manufacturer_article = await client.post(
        "/api/v1/articles",
        json={
            "name": "Lokaler Herstellerartikel",
            "category_id": category["id"],
            "manufacturer_name": "Synthetic Manufacturer",
            "manufacturer_part_number": "MPN-LOCAL-42",
        },
    )
    by_mpn = await client.post(
        "/api/v1/suppliers/mouser/search",
        json={"query": "MPN-LOCAL-42", "mode": "manufacturer_part_number"},
    )
    assert by_mpn.json()["local_matches"][0]["id"] == manufacturer_article.json()["id"]
    assert fake.calls == 0


@pytest.mark.anyio
async def test_multiple_results_are_escaped_and_require_selection(
    client: AsyncClient,
) -> None:
    fake = FakeAdapter(products("search_multiple.json"))
    set_adapter(client, fake)
    response = await client.post(
        "/api/v1/suppliers/mouser/search",
        json={"query": "synthetic capacitor", "mode": "keyword"},
    )
    assert response.status_code == 200
    assert len(response.json()["external_matches"]) == 2

    page = await client.get(
        "/suppliers/mouser", params={"q": "synthetic capacitor", "mode": "keyword"}
    )
    assert page.status_code == 200
    assert "&lt;script&gt;" in page.text
    assert "<script>alert" not in page.text
    assert page.text.count("Auswählen und prüfen") == 2

    review = await client.get(
        "/suppliers/mouser/review",
        params={"part_number": "80-SYNTH-100N-A"},
    )
    assert review.status_code == 200
    assert "Normalisiert aus „0.1 uF“" in review.text
    assert 'value="100"' in review.text
    assert ">nF</option>" in review.text
    assert "Abbrechen" in review.text
    assert (await client.get("/api/v1/articles")).json() == []


@pytest.mark.anyio
async def test_no_external_results_offer_manual_fallback(client: AsyncClient) -> None:
    set_adapter(client, FakeAdapter())
    response = await client.post(
        "/api/v1/suppliers/mouser/search",
        json={"query": "no-synthetic-hit", "mode": "keyword"},
    )
    assert response.status_code == 200
    assert response.json()["external_matches"] == []
    page = await client.get(
        "/suppliers/mouser", params={"q": "no-synthetic-hit", "mode": "keyword"}
    )
    assert "Keine Mouser-Treffer" in page.text
    assert "Manuell anlegen" in page.text


@pytest.mark.anyio
async def test_new_import_is_idempotent_and_does_not_change_inventory(
    client: AsyncClient,
) -> None:
    category = next(
        item
        for item in (await client.get("/api/v1/categories")).json()
        if item["code"] == "resistor"
    )
    payload = {
        "mouser_part_number": "71-SYNTH-10K",
        "name": "Synthetischer Importwiderstand",
        "category_id": category["id"],
        "manufacturer_name": "Synthetic Components",
        "manufacturer_part_number": "SYNTH-10K-0805",
        "product_url": "https://example.invalid/product",
        "attributes": [{"custom_name": "Importrohwert", "raw_value": "10000 Ohms"}],
    }
    first = await client.post(
        "/api/v1/suppliers/mouser/import",
        headers={"Idempotency-Key": "synthetic-import-1"},
        json=payload,
    )
    second = await client.post(
        "/api/v1/suppliers/mouser/import",
        headers={"Idempotency-Key": "synthetic-import-1"},
        json=payload,
    )
    assert first.status_code == second.status_code == 200
    assert first.json()["article_id"] == second.json()["article_id"]
    assert len((await client.get("/api/v1/articles")).json()) == 1
    assert (await client.get("/api/v1/inventory")).json() == []


@pytest.mark.anyio
async def test_mouser_number_can_be_linked_without_overwriting_existing_article(
    client: AsyncClient,
) -> None:
    category = next(
        item
        for item in (await client.get("/api/v1/categories")).json()
        if item["code"] == "other"
    )
    existing = await client.post(
        "/api/v1/articles",
        json={
            "name": "Bewusst lokale Bezeichnung",
            "category_id": category["id"],
            "description": "Lokale Beschreibung bleibt erhalten",
        },
    )
    linked = await client.post(
        "/api/v1/suppliers/mouser/import",
        headers={"Idempotency-Key": "synthetic-link-1"},
        json={
            "mouser_part_number": "71-LINK-ONLY",
            "existing_article_id": existing.json()["id"],
            "name": "Externe Bezeichnung wird ignoriert",
            "category_id": category["id"],
        },
    )
    assert linked.status_code == 200
    details = await client.get(f"/api/v1/articles/{existing.json()['id']}")
    assert details.json()["name"] == "Bewusst lokale Bezeichnung"
    assert details.json()["description"] == "Lokale Beschreibung bleibt erhalten"
    assert details.json()["supplier_parts"][0]["supplier_part_number"] == "71-LINK-ONLY"
    assert (await client.get("/api/v1/inventory")).json() == []
