import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_home_page_contains_branding_and_no_external_assets(
    client: AsyncClient,
) -> None:
    response = await client.get("/")

    assert response.status_code == 200
    assert "eBauteileFuchs" in response.text
    assert "Clever finden statt lange suchen." in response.text
    assert "eBauteileFuchs – ein Open-Source-Projekt von eHaJo" in response.text
    assert "fonts.googleapis.com" not in response.text
    assert "Maskottchen-Platzhalter" in response.text


@pytest.mark.anyio
async def test_static_branding_asset_is_served(client: AsyncClient) -> None:
    response = await client.get("/static/branding/ehajo-logo.svg")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
