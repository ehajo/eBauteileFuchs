import re

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_article_pages_create_search_and_edit(client: AsyncClient) -> None:
    choice = await client.get("/articles/new")
    assert choice.status_code == 200
    category_match = re.search(
        r'/articles/new\?category_id=([^"\s]+)[^>]*><strong>Widerstand',
        choice.text,
    )
    assert category_match is not None

    form = await client.get(
        "/articles/new", params={"category_id": category_match.group(1)}
    )
    assert form.status_code == 200
    assert "Widerstandswert" in form.text
    assert "autofocus" in form.text
    token = re.search(r'name="csrf_token" value="([^"]+)"', form.text)
    assert token is not None

    resistance = re.search(r'name="attribute_([^"]+)"[^>]*', form.text)
    supplier = re.search(r'<option value="([^"]+)"[^>]*>Mouser Electronics', form.text)
    assert resistance is not None
    assert supplier is not None
    created = await client.post(
        "/articles",
        data={
            "csrf_token": token.group(1),
            "name": "Widerstand 10 kΩ 0805",
            "category_id": category_match.group(1),
            "manufacturer_name": "Vishay",
            "manufacturer_part_number": "CRCW0805-10K0-FKEA",
            f"attribute_{resistance.group(1)}": "10 kΩ",
            f"unit_{resistance.group(1)}": "Ω",
            "supplier_id_1": supplier.group(1),
            "supplier_number_1": "71-CRCW0805-10K-E3",
            "description": "Synthetischer Testartikel",
        },
        follow_redirects=True,
    )
    assert created.status_code == 200, created.text
    assert "Technische Eigenschaften" in created.text
    assert "10 kΩ" in created.text

    search = await client.get("/articles", params={"q": "10 kΩ"})
    assert search.status_code == 200
    assert "Widerstand 10 kΩ 0805" in search.text

    edit_link = re.search(r'href="(/articles/[^"]+/edit)"', created.text)
    assert edit_link is not None
    edit = await client.get(edit_link.group(1))
    assert edit.status_code == 200
    assert "CRCW0805-10K0-FKEA" in edit.text


@pytest.mark.anyio
async def test_direct_child_location_link_preselects_parent(
    client: AsyncClient,
) -> None:
    types = (await client.get("/api/v1/location-types")).json()
    room_type = next(item["id"] for item in types if item["code"] == "room")
    created = await client.post(
        "/api/v1/locations",
        json={
            "code": "R-DIREKT",
            "name": "Direkter Raum",
            "location_type_id": room_type,
        },
    )
    detail = await client.get(f"/locations/{created.json()['id']}")
    assert "Unterplatz anlegen" in detail.text
    child_form = await client.get(
        "/locations/new", params={"parent_id": created.json()["id"]}
    )
    assert re.search(
        rf'<option value="{created.json()["id"]}" selected>', child_form.text
    )
