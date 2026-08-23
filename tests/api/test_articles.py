import pytest
from httpx import AsyncClient


async def _category(client: AsyncClient, code: str) -> dict:
    response = await client.get("/api/v1/categories")
    assert response.status_code == 200
    return next(item for item in response.json() if item["code"] == code)


async def _attribute(client: AsyncClient, category_id: str, code: str) -> dict:
    response = await client.get(f"/api/v1/categories/{category_id}/attributes")
    assert response.status_code == 200
    return next(item for item in response.json() if item["code"] == code)


async def _mouser(client: AsyncClient) -> dict:
    response = await client.get("/api/v1/suppliers")
    assert response.status_code == 200
    return next(item for item in response.json() if item["code"] == "mouser")


async def _resistor_payload(client: AsyncClient) -> dict:
    category = await _category(client, "resistor")
    resistance = await _attribute(client, category["id"], "resistance")
    package = await _attribute(client, category["id"], "package")
    supplier = await _mouser(client)
    return {
        "name": "Präzisionswiderstand 10 kΩ 0805",
        "category_id": category["id"],
        "manufacturer_name": "Vishay",
        "manufacturer_part_number": "CRCW0805-10K0-FKEA",
        "description": "Synthetischer Testartikel",
        "datasheet_url": "https://example.invalid/datasheet.pdf",
        "attributes": [
            {
                "definition_id": resistance["id"],
                "raw_value": "10 kΩ",
                "unit": "Ω",
            },
            {"definition_id": package["id"], "raw_value": "0805"},
            {"custom_name": "Lagerhinweis", "raw_value": "trocken"},
        ],
        "supplier_parts": [
            {
                "supplier_id": supplier["id"],
                "supplier_part_number": "71-CRCW0805-10K-E3",
                "product_url": "https://example.invalid/product",
            }
        ],
    }


@pytest.mark.anyio
async def test_reference_data_and_article_crud_search(client: AsyncClient) -> None:
    categories = await client.get("/api/v1/categories")
    assert len(categories.json()) == 10
    resistor = await _category(client, "resistor")
    attributes = await client.get(f"/api/v1/categories/{resistor['id']}/attributes")
    assert {item["code"] for item in attributes.json()} >= {
        "resistance",
        "tolerance",
        "power",
        "package",
    }

    payload = await _resistor_payload(client)
    created = await client.post("/api/v1/articles", json=payload)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["manufacturer"]["name"] == "Vishay"
    assert body["manufacturer"]["normalized_name"] == "vishay"
    assert body["normalized_manufacturer_part_number"] == "CRCW080510K0FKEA"
    assert len(body["attributes"]) == 3
    assert body["supplier_parts"][0]["supplier_part_number"] == "71-CRCW0805-10K-E3"

    search = await client.get("/api/v1/articles", params={"q": "10 kΩ 0805"})
    assert search.status_code == 200
    assert [item["id"] for item in search.json()] == [body["id"]]

    payload["description"] = "Bearbeiteter synthetischer Testartikel"
    payload["note"] = "Nur für automatisierte Tests"
    updated = await client.put(f"/api/v1/articles/{body['id']}", json=payload)
    assert updated.status_code == 200, updated.text
    assert updated.json()["description"].startswith("Bearbeiteter")
    assert updated.json()["note"] == "Nur für automatisierte Tests"


@pytest.mark.anyio
async def test_duplicate_detection_levels_and_explicit_similarity_override(
    client: AsyncClient,
) -> None:
    payload = await _resistor_payload(client)
    created = await client.post("/api/v1/articles", json=payload)
    assert created.status_code == 201

    exact_supplier = payload | {
        "name": "Anderer Name",
        "manufacturer_part_number": "ANDERE-NUMMER",
    }
    response = await client.post("/api/v1/articles", json=exact_supplier)
    assert response.status_code == 409
    assert response.json()["match_level"] == 1
    assert response.json()["can_override"] is False

    normalized_identity = payload | {
        "name": "Noch ein anderer Name",
        "manufacturer_name": "  VISHAY ",
        "manufacturer_part_number": "crcw 0805 / 10k0_fkea",
        "supplier_parts": [],
    }
    response = await client.post("/api/v1/articles", json=normalized_identity)
    assert response.status_code == 409
    assert response.json()["match_level"] == 3

    similar = payload | {
        "manufacturer_name": None,
        "manufacturer_part_number": None,
        "supplier_parts": [],
        "name": "Präzisionswiderstand 10 kΩ 0806",
    }
    warning = await client.post("/api/v1/articles", json=similar)
    assert warning.status_code == 409
    assert warning.json()["match_level"] == 4
    assert warning.json()["can_override"] is True

    similar["acknowledge_similar"] = True
    accepted = await client.post("/api/v1/articles", json=similar)
    assert accepted.status_code == 201, accepted.text


@pytest.mark.anyio
async def test_manufacturer_category_and_validation_contracts(
    client: AsyncClient,
) -> None:
    manufacturer = await client.post(
        "/api/v1/manufacturers", json={"name": "Texas Instruments"}
    )
    assert manufacturer.status_code == 201
    updated = await client.put(
        f"/api/v1/manufacturers/{manufacturer.json()['id']}",
        json={"name": "Texas Instruments Incorporated", "is_active": False},
    )
    assert updated.status_code == 200
    assert updated.json()["is_active"] is False

    category = await client.post(
        "/api/v1/categories",
        json={
            "code": "module",
            "name": "Modul",
            "description": "Zusammengesetzte Module",
            "sort_order": 110,
        },
    )
    assert category.status_code == 201
    assert category.json()["is_system"] is False

    invalid = await client.post(
        "/api/v1/articles",
        json={
            "name": "Ungültiger Link",
            "category_id": category.json()["id"],
            "datasheet_url": "javascript:alert(1)",
        },
    )
    assert invalid.status_code == 422
    assert "HTTP- oder HTTPS" in invalid.json()["detail"]


@pytest.mark.anyio
async def test_referenced_category_can_be_deactivated_without_losing_article(
    client: AsyncClient,
) -> None:
    category = await client.post(
        "/api/v1/categories",
        json={"code": "sensor", "name": "Sensor", "sort_order": 120},
    )
    article = await client.post(
        "/api/v1/articles",
        json={"name": "Synthetischer Sensor", "category_id": category.json()["id"]},
    )
    assert article.status_code == 201

    deactivated = await client.put(
        f"/api/v1/categories/{category.json()['id']}",
        json={
            "name": "Sensor",
            "description": None,
            "sort_order": 120,
            "is_active": False,
        },
    )
    assert deactivated.status_code == 200
    assert (
        await client.get(f"/api/v1/articles/{article.json()['id']}")
    ).status_code == 200

    rejected = await client.post(
        "/api/v1/articles",
        json={"name": "Weiterer Sensor", "category_id": category.json()["id"]},
    )
    assert rejected.status_code == 404
