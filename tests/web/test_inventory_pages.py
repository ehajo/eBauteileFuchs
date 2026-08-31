import html
import re

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_inventory_pages_and_qr_entry_show_mobile_booking_actions(
    client: AsyncClient,
) -> None:
    category = next(
        item
        for item in (await client.get("/api/v1/categories")).json()
        if item["code"] == "other"
    )
    article = (
        await client.post(
            "/api/v1/articles",
            json={"name": "Synthetisches Scanbauteil", "category_id": category["id"]},
        )
    ).json()
    drawer_type = next(
        item
        for item in (await client.get("/api/v1/location-types")).json()
        if item["code"] == "drawer"
    )
    location = (
        await client.post(
            "/api/v1/locations",
            json={
                "code": "SCAN-01",
                "name": "Scanschublade",
                "location_type_id": drawer_type["id"],
            },
        )
    ).json()

    form = await client.get(
        "/inventory/stock-in",
        params={"article_id": article["id"], "location_id": location["id"]},
    )
    assert form.status_code == 200
    assert "Schnellbuchung" in form.text
    assert "−5" in form.text
    assert "−1" in form.text
    assert "+1" in form.text
    assert "+5" in form.text
    assert 'name="idempotency_key"' in form.text
    assert 'inputmode="decimal"' in form.text
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', form.text).group(1)
    booking = re.search(r'name="idempotency_key" value="([^"]+)"', form.text).group(1)
    booked = await client.post(
        "/inventory/book",
        data={
            "csrf_token": csrf,
            "idempotency_key": booking,
            "article_id": article["id"],
            "location_id": location["id"],
            "quantity": "100",
            "operation": "stock-in",
            "unit": "Stück",
        },
    )
    assert booked.status_code == 200, booked.text
    assert "Bestand geändert" in booked.text
    assert "+100 Stück" in booked.text
    assert "1E+2" not in booked.text
    assert "jetzt" in booked.text

    next_booking = re.search(
        r'name="idempotency_key" value="([^"]+)"', booked.text
    ).group(1)
    removed = await client.post(
        "/inventory/book",
        data={
            "csrf_token": csrf,
            "idempotency_key": next_booking,
            "article_id": article["id"],
            "location_id": location["id"],
            "delta": "-5",
            "unit": "Stück",
        },
    )
    assert removed.status_code == 200
    assert "-5 Stück" in removed.text
    assert "jetzt <strong>95 Stück</strong>" in removed.text

    article_page = await client.get(f"/articles/{article['id']}")
    assert "95" in article_page.text
    assert "1E+2" not in article_page.text
    assert "Umlagern" in article_page.text
    qr_entry = await client.get(location["qr_path"], follow_redirects=True)
    assert "Synthetisches Scanbauteil" in qr_entry.text
    assert "Bestand hier ändern" in qr_entry.text


@pytest.mark.anyio
async def test_inventory_search_preserves_location_and_stock_out_filters_locations(
    client: AsyncClient,
) -> None:
    category = next(
        item
        for item in (await client.get("/api/v1/categories")).json()
        if item["code"] == "other"
    )
    article = (
        await client.post(
            "/api/v1/articles",
            json={"name": "Synthetischer Suchartikel", "category_id": category["id"]},
        )
    ).json()
    drawer_type = next(
        item
        for item in (await client.get("/api/v1/location-types")).json()
        if item["code"] == "drawer"
    )
    stocked_location = (
        await client.post(
            "/api/v1/locations",
            json={
                "code": "BESTAND-01",
                "name": "Schublade mit Bestand",
                "location_type_id": drawer_type["id"],
            },
        )
    ).json()
    empty_location = await client.post(
        "/api/v1/locations",
        json={
            "code": "LEER-01",
            "name": "Leere Schublade",
            "location_type_id": drawer_type["id"],
        },
    )
    assert empty_location.status_code == 201

    stock_in = await client.get(
        "/inventory/stock-in",
        params={"article_id": article["id"], "location_id": stocked_location["id"]},
    )
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', stock_in.text).group(1)
    booking = re.search(r'name="idempotency_key" value="([^"]+)"', stock_in.text).group(
        1
    )
    booked = await client.post(
        "/inventory/stock-in",
        data={
            "csrf_token": csrf,
            "idempotency_key": booking,
            "article_id": article["id"],
            "location_id": stocked_location["id"],
            "quantity": "3",
            "unit": "Stück",
        },
    )
    assert booked.status_code == 200

    search = await client.get(
        "/inventory/stock-in",
        params={
            "q": "Suchartikel",
            "location_id": stocked_location["id"],
        },
    )
    assert search.status_code == 200
    assert "Artikel auswählen" in search.text
    choice_match = re.search(
        rf'href="([^"]*inventory/book[^"]*article_id={article["id"]}[^"]*)"',
        search.text,
    )
    assert choice_match is not None
    choice_url = html.unescape(choice_match.group(1))
    assert f"location_id={stocked_location['id']}" in choice_url

    selected = await client.get(choice_url)
    assert "Ausgewählter Artikel" in selected.text
    assert "Synthetischer Suchartikel" in selected.text
    assert re.search(
        rf'<option value="{stocked_location["id"]}"[^>]* selected>', selected.text
    )

    stock_out = await client.get(
        "/inventory/book", params={"article_id": article["id"]}
    )
    assert stock_out.status_code == 200
    quick_select = re.search(
        r'<select id="quick-location" name="location_id".*?</select>',
        stock_out.text,
        re.DOTALL,
    ).group(0)
    assert "BESTAND-01" in quick_select
    assert "LEER-01" not in quick_select

    start_page = await client.get("/")
    assert 'href="/inventory"' in start_page.text


@pytest.mark.anyio
async def test_stock_in_filters_leaf_locations_and_selects_next_free_in_scope(
    client: AsyncClient,
) -> None:
    category = next(
        item
        for item in (await client.get("/api/v1/categories")).json()
        if item["code"] == "other"
    )
    article = (
        await client.post(
            "/api/v1/articles",
            json={"name": "Artikel für freie Box", "category_id": category["id"]},
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
        assert response.status_code == 201
        return response.json()

    room = await location("RAUM-A", "room")
    shelf = await location("REGAL-1", "shelf", room["id"])
    occupied = await location("BOX-01", "box", shelf["id"])
    free = await location("BOX-02", "box", shelf["id"])
    other_room = await location("RAUM-B", "room")
    other_box = await location("BOX-99", "box", other_room["id"])

    booked = await client.post(
        "/api/v1/inventory/stock-in",
        headers={"Idempotency-Key": "occupied-location-1"},
        json={
            "article_id": article["id"],
            "location_id": occupied["id"],
            "quantity": "1",
        },
    )
    assert booked.status_code == 201

    page = await client.get(
        "/inventory/book",
        params={
            "article_id": article["id"],
            "location_scope_id": room["id"],
            "choose_free": "1",
        },
    )
    assert page.status_code == 200
    assert "Nächster freier Platz vorausgewählt" in page.text
    select = re.search(
        r'<select id="quick-location" name="location_id".*?</select>',
        page.text,
        re.DOTALL,
    ).group(0)
    assert occupied["id"] in select
    assert free["id"] in select
    assert re.search(rf'<option value="{free["id"]}"[^>]*selected', select)
    assert room["id"] not in select
    assert shelf["id"] not in select
    assert other_box["id"] not in select
