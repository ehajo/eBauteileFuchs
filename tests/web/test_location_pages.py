import re

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_location_pages_and_keyboard_friendly_form(client: AsyncClient) -> None:
    overview = await client.get("/locations")
    assert overview.status_code == 200
    assert "Noch keine Lagerplätze" in overview.text
    assert "Magazin-Assistent" in overview.text

    form = await client.get("/locations/new")
    assert form.status_code == 200
    assert 'name="code"' in form.text
    assert "autofocus" in form.text
    token = re.search(r'name="csrf_token" value="([^"]+)"', form.text)
    assert token is not None
    room_type = re.search(r'<option value="([^"]+)"[^>]*>Raum', form.text)
    assert room_type is not None

    created = await client.post(
        "/locations",
        data={
            "csrf_token": token.group(1),
            "code": "R1",
            "name": "Werkstatt",
            "location_type_id": room_type.group(1),
            "parent_id": "",
            "description": "Der Hauptraum",
        },
        follow_redirects=True,
    )
    assert created.status_code == 200
    assert "Werkstatt" in created.text
    assert "QR-Code" in created.text

    populated_overview = await client.get("/locations")
    assert populated_overview.status_code == 200
    assert "R1" in populated_overview.text


@pytest.mark.anyio
async def test_html_form_rejects_csrf_and_shows_validation(client: AsyncClient) -> None:
    rejected = await client.post(
        "/locations",
        data={
            "csrf_token": "wrong",
            "code": "R1",
            "name": "Werkstatt",
            "location_type_id": "10000000-0000-4000-8000-000000000001",
        },
    )
    assert rejected.status_code == 403

    form = await client.get("/locations/new")
    token = re.search(r'name="csrf_token" value="([^"]+)"', form.text)
    assert token is not None
    invalid = await client.post(
        "/locations",
        data={
            "csrf_token": token.group(1),
            "code": "   ",
            "name": "Werkstatt",
            "location_type_id": "10000000-0000-4000-8000-000000000001",
        },
    )
    assert invalid.status_code == 422
    assert "Kennung darf nicht leer sein" in invalid.text


@pytest.mark.anyio
async def test_unused_location_can_be_deleted(client: AsyncClient) -> None:
    drawer_type = next(
        item
        for item in (await client.get("/api/v1/location-types")).json()
        if item["code"] == "drawer"
    )
    location = (
        await client.post(
            "/api/v1/locations",
            json={
                "code": "LOESCH-01",
                "name": "Unbenutzte Schublade",
                "location_type_id": drawer_type["id"],
            },
        )
    ).json()

    detail = await client.get(f"/locations/{location['id']}")
    assert detail.status_code == 200
    assert f"/locations/{location['id']}/delete" in detail.text

    confirmation = await client.get(f"/locations/{location['id']}/delete")
    token = re.search(r'name="csrf_token" value="([^"]+)"', confirmation.text)
    assert token is not None
    deleted = await client.post(
        f"/locations/{location['id']}/delete",
        data={"csrf_token": token.group(1), "confirm": "yes"},
        follow_redirects=True,
    )
    assert deleted.status_code == 200
    assert "LOESCH-01" not in deleted.text
    assert (await client.get(f"/api/v1/locations/{location['id']}")).status_code == 404


@pytest.mark.anyio
async def test_location_with_child_cannot_be_deleted(client: AsyncClient) -> None:
    room_type = next(
        item
        for item in (await client.get("/api/v1/location-types")).json()
        if item["code"] == "room"
    )
    shelf_type = next(
        item
        for item in (await client.get("/api/v1/location-types")).json()
        if item["code"] == "shelf"
    )
    parent = (
        await client.post(
            "/api/v1/locations",
            json={
                "code": "RAUM-LOESCH",
                "name": "Raum mit Unterplatz",
                "location_type_id": room_type["id"],
            },
        )
    ).json()
    child = await client.post(
        "/api/v1/locations",
        json={
            "code": "REGAL-LOESCH",
            "name": "Untergeordnetes Regal",
            "location_type_id": shelf_type["id"],
            "parent_id": parent["id"],
        },
    )
    assert child.status_code == 201

    confirmation = await client.get(f"/locations/{parent['id']}/delete")
    token = re.search(r'name="csrf_token" value="([^"]+)"', confirmation.text)
    assert token is not None
    rejected = await client.post(
        f"/locations/{parent['id']}/delete",
        data={"csrf_token": token.group(1), "confirm": "yes"},
    )
    assert rejected.status_code == 409
    assert "Entferne zuerst alle Unterplätze" in rejected.text
    assert (await client.get(f"/api/v1/locations/{parent['id']}")).status_code == 200
