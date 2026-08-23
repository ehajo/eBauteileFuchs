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
