import re

import pytest
from httpx import AsyncClient


async def _type_id(client: AsyncClient, code: str) -> str:
    items = (await client.get("/api/v1/location-types")).json()
    return next(item["id"] for item in items if item["code"] == code)


async def _location(
    client: AsyncClient, code: str, type_code: str, parent_id: str | None = None
) -> dict:
    response = await client.post(
        "/api/v1/locations",
        json={
            "code": code,
            "name": f"Test {code}",
            "location_type_id": await _type_id(client, type_code),
            "parent_id": parent_id,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _article(client: AsyncClient, name: str) -> dict:
    categories = (await client.get("/api/v1/categories")).json()
    category_id = next(item["id"] for item in categories if item["code"] == "other")
    response = await client.post(
        "/api/v1/articles", json={"name": name, "category_id": category_id}
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _stock(client: AsyncClient, article_id: str, location_id: str, key: str):
    response = await client.post(
        "/api/v1/inventory/stock-in",
        json={
            "article_id": article_id,
            "location_id": location_id,
            "quantity": "7",
        },
        headers={"Idempotency-Key": key},
    )
    assert response.status_code == 201, response.text


@pytest.mark.anyio
async def test_magazine_assistant_creates_parent_and_grouping_reparents_siblings(
    client: AsyncClient,
) -> None:
    room = await _location(client, "ROOM-MAG", "room")
    first = await _location(client, "OLD-01", "drawer", room["id"])
    second = await _location(client, "OLD-02", "drawer", room["id"])
    page = await client.get("/locations")
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
    grouped = await client.post(
        "/locations/group",
        data={
            "csrf_token": csrf,
            "location_ids": [first["id"], second["id"]],
            "code": "MAG-ALT",
            "name": "Bestehendes Magazin",
        },
        follow_redirects=True,
    )
    assert grouped.status_code == 200, grouped.text
    assert "Bestehendes Magazin" in grouped.text
    tree = (await client.get("/api/v1/locations/tree")).json()
    room_node = next(item for item in tree if item["location"]["id"] == room["id"])
    magazine = next(
        item for item in room_node["children"] if item["location"]["code"] == "MAG-ALT"
    )
    assert {item["location"]["code"] for item in magazine["children"]} == {
        "OLD-01",
        "OLD-02",
    }

    assistant = await client.get("/locations/magazine/new")
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', assistant.text).group(1)
    drawer_type = await _type_id(client, "drawer")
    created = await client.post(
        "/locations/magazine/create",
        data={
            "csrf_token": csrf,
            "parent_id": room["id"],
            "location_type_id": drawer_type,
            "magazine_code": "MAG-NEU",
            "magazine_name": "Neues Magazin",
            "count": "2",
            "start_number": "1",
            "padding": "2",
            "code_pattern": "{number_padded}",
            "name_pattern": "Schublade {number_padded}",
        },
        follow_redirects=True,
    )
    assert created.status_code == 200
    assert "3 Lagerplätze wurden angelegt" in created.text
    tree = (await client.get("/api/v1/locations/tree")).json()
    room_node = next(item for item in tree if item["location"]["id"] == room["id"])
    magazine = next(
        item for item in room_node["children"] if item["location"]["code"] == "MAG-NEU"
    )
    assert [item["location"]["code"] for item in magazine["children"]] == [
        "01",
        "02",
    ]


@pytest.mark.anyio
async def test_recursive_safe_delete_handles_all_article_choices(
    client: AsyncClient,
) -> None:
    room = await _location(client, "ROOM-DEL", "room")
    drawers = [
        await _location(client, f"DEL-{number}", "drawer", room["id"])
        for number in range(1, 4)
    ]
    target = await _location(client, "KEEP-TARGET", "box")
    articles = [
        await _article(client, name)
        for name in ("Ohne Ort erhalten", "Neu zuweisen", "Ganz entfernen")
    ]
    for index, (article, drawer) in enumerate(zip(articles, drawers, strict=True)):
        await _stock(client, article["id"], drawer["id"], f"archive-stock-{index}")
    await _stock(client, articles[2]["id"], target["id"], "archive-stock-outside")

    page = await client.get("/locations")
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
    preview = await client.post(
        "/locations/archive/preview",
        data={"csrf_token": csrf, "location_ids": room["id"]},
    )
    assert preview.status_code == 200, preview.text
    assert "4 Lagerplätze einschließlich Unterplätzen" in preview.text
    assert all(article["name"] in preview.text for article in articles)
    booking_key = re.search(
        r'name="idempotency_key" value="([^"]+)"', preview.text
    ).group(1)
    archived = await client.post(
        "/locations/archive",
        data={
            "csrf_token": csrf,
            "idempotency_key": booking_key,
            "location_ids": room["id"],
            f"action_{articles[0]['id']}": "keep_unassigned",
            f"action_{articles[1]['id']}": "assign",
            f"target_{articles[1]['id']}": target["id"],
            f"action_{articles[2]['id']}": "delete_article",
        },
        follow_redirects=True,
    )
    assert archived.status_code == 200, archived.text
    assert "4 Lagerplätze wurden sicher archiviert" in archived.text
    assert "ROOM-DEL" not in archived.text

    positions = (await client.get("/api/v1/inventory")).json()
    by_article = {item["article_id"]: item for item in positions}
    assert by_article[articles[0]["id"]]["location_code"] == "OHNE-LAGERPLATZ"
    assert by_article[articles[1]["id"]]["location_code"] == "KEEP-TARGET"
    assert articles[2]["id"] not in by_article
    deleted_article = await client.get(f"/api/v1/articles/{articles[2]['id']}")
    assert deleted_article.status_code == 200
    assert deleted_article.json()["is_active"] is False
    archived_room = await client.get(f"/api/v1/locations/{room['id']}")
    assert archived_room.status_code == 200
    assert archived_room.json()["is_active"] is False
    journal = (await client.get("/api/v1/inventory/transactions")).json()
    assert any(
        item["comment"] == "Lagerplätze revisionssicher archiviert" for item in journal
    )
