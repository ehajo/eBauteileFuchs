from io import BytesIO

import pytest
from httpx import AsyncClient
from pypdf import PdfReader


async def _type_id(client: AsyncClient, code: str) -> str:
    response = await client.get("/api/v1/location-types")
    return next(item["id"] for item in response.json() if item["code"] == code)


async def _create_location(
    client: AsyncClient,
    *,
    code: str,
    name: str,
    type_code: str,
    parent_id: str | None = None,
) -> dict:
    response = await client.post(
        "/api/v1/locations",
        json={
            "code": code,
            "name": name,
            "location_type_id": await _type_id(client, type_code),
            "parent_id": parent_id,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.anyio
async def test_location_hierarchy_validation_and_deactivation(
    client: AsyncClient,
) -> None:
    room = await _create_location(
        client, code="RAUM-1", name="Werkstatt", type_code="room"
    )
    cabinet = await _create_location(
        client,
        code="S1",
        name="Bauteileschrank",
        type_code="cabinet",
        parent_id=room["id"],
    )

    duplicate = await client.post(
        "/api/v1/locations",
        json={
            "code": " s1 ",
            "name": "Doppelt",
            "location_type_id": await _type_id(client, "cabinet"),
            "parent_id": room["id"],
        },
    )
    assert duplicate.status_code == 409
    assert "bereits vorhanden" in duplicate.json()["detail"]

    cycle = await client.patch(
        f"/api/v1/locations/{room['id']}", json={"parent_id": cabinet["id"]}
    )
    assert cycle.status_code == 409
    assert "Unterplatz" in cycle.json()["detail"]

    blocked = await client.delete(f"/api/v1/locations/{room['id']}")
    assert blocked.status_code == 409
    assert "aktive Unterplätze" in blocked.json()["detail"]

    assert (
        await client.delete(f"/api/v1/locations/{cabinet['id']}")
    ).status_code == 200
    assert (await client.delete(f"/api/v1/locations/{room['id']}")).status_code == 200
    activated = await client.post(f"/api/v1/locations/{cabinet['id']}/activate")
    assert activated.status_code == 409
    assert "Aktiviere ihn zuerst" in activated.json()["detail"]


@pytest.mark.anyio
async def test_location_tree_qr_and_pdf_labels(client: AsyncClient) -> None:
    room = await _create_location(client, code="R1", name="Labor", type_code="room")
    drawer = await _create_location(
        client,
        code="01",
        name="Schublade 01",
        type_code="drawer",
        parent_id=room["id"],
    )

    tree = (await client.get("/api/v1/locations/tree")).json()
    assert tree[0]["location"]["code"] == "R1"
    assert tree[0]["children"][0]["location"]["code"] == "01"
    assert drawer["path"][-1]["name"] == "Schublade 01"

    qr_first = await client.get(f"/api/v1/locations/{drawer['id']}/qr.svg")
    qr_second = await client.get(f"/api/v1/locations/{drawer['id']}/qr.svg")
    assert qr_first.status_code == 200
    assert qr_first.content == qr_second.content
    assert qr_first.content.startswith(b"<?xml")

    resolved = await client.get(drawer["qr_path"], follow_redirects=False)
    assert resolved.status_code == 303
    assert resolved.headers["location"] == f"/locations/{drawer['id']}"

    single = await client.get(f"/api/v1/locations/{drawer['id']}/label.pdf")
    assert single.content.startswith(b"%PDF")
    assert len(PdfReader(BytesIO(single.content)).pages) == 1

    sheet = await client.post(
        "/api/v1/locations/labels.pdf",
        json={"location_ids": [room["id"], drawer["id"]]},
    )
    assert sheet.status_code == 200
    assert len(PdfReader(BytesIO(sheet.content)).pages) == 1


@pytest.mark.anyio
async def test_magazine_batch_preview_create_and_atomic_conflict(
    client: AsyncClient,
) -> None:
    magazine = await _create_location(
        client, code="MAG-1", name="Magazin", type_code="magazine"
    )
    payload = {
        "parent_id": magazine["id"],
        "location_type_id": await _type_id(client, "drawer"),
        "count": 60,
        "start_number": 1,
        "padding": 2,
        "code_pattern": "{number_padded}",
        "name_pattern": "Schublade {number_padded}",
    }

    preview = await client.post("/api/v1/locations/batch/preview", json=payload)
    assert preview.status_code == 200
    assert len(preview.json()["items"]) == 60
    assert preview.json()["items"][0]["code"] == "01"
    assert preview.json()["items"][-1]["code"] == "60"
    assert preview.json()["has_conflicts"] is False

    created = await client.post("/api/v1/locations/batch", json=payload)
    assert created.status_code == 201
    assert len(created.json()) == 60

    conflict = await client.post("/api/v1/locations/batch", json=payload)
    assert conflict.status_code == 409
    locations = (await client.get("/api/v1/locations")).json()
    assert len(locations) == 61


@pytest.mark.anyio
async def test_custom_type_and_controlled_invalid_input(client: AsyncClient) -> None:
    custom = await client.post(
        "/api/v1/location-types",
        json={"code": "rollwagen", "name": "Rollwagen", "sort_order": 90},
    )
    assert custom.status_code == 201
    assert custom.json()["is_system"] is False

    updated_type = await client.put(
        f"/api/v1/location-types/{custom.json()['id']}",
        json={"name": "Mobiler Rollwagen", "sort_order": 95, "is_active": False},
    )
    assert updated_type.status_code == 200
    assert updated_type.json()["name"] == "Mobiler Rollwagen"
    assert updated_type.json()["is_active"] is False

    invalid = await client.post(
        "/api/v1/locations",
        json={
            "code": "   ",
            "name": "Ungültig",
            "location_type_id": await _type_id(client, "room"),
        },
    )
    assert invalid.status_code == 422
    assert "Kennung darf nicht leer" in invalid.json()["detail"]

    null_patch = await client.patch(
        "/api/v1/locations/00000000-0000-4000-8000-000000000000",
        json={"code": None},
    )
    assert null_patch.status_code == 422


@pytest.mark.anyio
async def test_cross_origin_write_is_rejected(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/location-types",
        headers={"Origin": "https://example.invalid"},
        json={"code": "fremd", "name": "Fremd", "sort_order": 100},
    )
    assert response.status_code == 403
    assert "fremden Website" in response.json()["detail"]
