import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_data_page_lists_exports_and_restore_safety(client: AsyncClient) -> None:
    response = await client.get("/data")
    assert response.status_code == 200
    assert "Daten verwalten" in response.text
    assert "/data/exports/article-properties" in response.text
    assert "automatisch eine Vorsicherung" in response.text
    assert (
        'class="button" type="submit">Vollständige Sicherung erstellen' in response.text
    )


@pytest.mark.anyio
async def test_restore_preview_requires_csrf(client: AsyncClient) -> None:
    response = await client.post(
        "/data/restore/preview",
        data={"csrf_token": "wrong"},
        files={"backup_file": ("backup.zip", b"invalid", "application/zip")},
    )
    assert response.status_code == 403
