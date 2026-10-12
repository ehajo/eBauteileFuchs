import pytest
from httpx import AsyncClient


async def _article(client: AsyncClient) -> dict:
    categories = (await client.get("/api/v1/categories")).json()
    category = next(item for item in categories if item["code"] == "resistor")
    response = await client.post(
        "/api/v1/articles",
        json={"name": "Startseiten-Widerstand", "category_id": category["id"]},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _location(client: AsyncClient) -> dict:
    location_types = (await client.get("/api/v1/location-types")).json()
    drawer_type = next(item for item in location_types if item["code"] == "drawer")
    response = await client.post(
        "/api/v1/locations",
        json={
            "code": "HOME-01",
            "name": "Startseitenfach",
            "location_type_id": drawer_type["id"],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.anyio
async def test_home_page_is_a_functional_storage_dashboard(
    client: AsyncClient,
) -> None:
    response = await client.get("/")

    assert response.status_code == 200
    assert "Deine Lagerzentrale" in response.text
    assert "Bauteil finden" in response.text
    assert "Name, Artikelnummer, Eigenschaft oder Lagerplatz" in response.text
    assert "Barcode scannen" in response.text
    assert "Schnellaktionen" in response.text
    assert "Lagerübersicht" in response.text
    assert "Letzte Bewegungen" in response.text
    assert "Erstes Bauteil einlagern" in response.text
    assert "Projektstatus" not in response.text
    assert "Verbindung · M5" not in response.text
    assert "Idempotente Buchungen" not in response.text
    assert 'href="/inventory/book"' in response.text
    assert 'href="/inventory/transfer"' in response.text
    assert 'href="/articles/new"' in response.text
    assert 'href="/locations"' in response.text
    assert 'data-scan-url="/suppliers/mouser?mode=barcode&amp;q="' in response.text
    assert 'capture="environment"' in response.text
    assert "fonts.googleapis.com" not in response.text
    assert "Fuchs-Maskottchen von eBauteileFuchs" not in response.text
    assert "/static/branding/fuchs-maskottchen.png" in response.text


@pytest.mark.anyio
async def test_home_page_shows_actual_statistics_and_latest_movement(
    client: AsyncClient,
) -> None:
    article = await _article(client)
    location = await _location(client)
    booking = await client.post(
        "/api/v1/inventory/stock-in",
        json={
            "article_id": article["id"],
            "location_id": location["id"],
            "quantity": "7",
        },
        headers={"Idempotency-Key": "home-dashboard-stock-in-0001"},
    )
    assert booking.status_code == 201, booking.text

    response = await client.get("/")

    assert "Startseiten-Widerstand" in response.text
    assert "HOME-01" in response.text
    assert "Einlagerung" in response.text
    assert "+7 Stück" in response.text
    assert "aktive Artikel" in response.text
    assert "aktive Plätze" in response.text
    assert "mit Bestand" in response.text


@pytest.mark.anyio
async def test_home_page_keeps_local_barcode_assets_and_responsive_structure(
    client: AsyncClient,
) -> None:
    response = await client.get("/")
    styles = await client.get("/static/css/app.css")

    assert response.status_code == styles.status_code == 200
    assert "vendor/zxing-wasm/reader.js" in response.text
    assert response.text.index("vendor/zxing-wasm/reader.js") < response.text.index(
        "js/barcode-scanner.js"
    )
    assert "fastly.jsdelivr.net" not in response.text
    assert ".home-search__row" in styles.text
    assert ".home-actions" in styles.text
    assert ".home-statistics" in styles.text
    assert "@media (max-width: 48rem)" in styles.text


@pytest.mark.anyio
async def test_static_branding_asset_is_served(client: AsyncClient) -> None:
    response = await client.get("/static/branding/ehajo-logo.svg")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")


@pytest.mark.anyio
async def test_local_photo_barcode_decoder_is_served(client: AsyncClient) -> None:
    script = await client.get("/static/vendor/zxing-wasm/reader.js")
    wasm = await client.get("/static/vendor/zxing-wasm/zxing_reader.wasm")
    scanner = await client.get("/static/js/barcode-scanner.js")
    styles = await client.get("/static/css/app.css")

    assert script.status_code == wasm.status_code == scanner.status_code == 200
    assert styles.status_code == 200
    assert wasm.headers["content-type"] == "application/wasm"
    assert len(wasm.content) == 1_093_289
    assert "fastly.jsdelivr.net" not in scanner.text
    assert 'WASM_URL = "/static/vendor/zxing-wasm/zxing_reader.wasm?v=3.1.3"' in (
        scanner.text
    )
    assert "createImageBitmap" in scanner.text
    assert "maxNumberOfSymbols: 8" in scanner.text
    assert "activeInput.blur()" in scanner.text


@pytest.mark.anyio
async def test_about_page_reports_the_release_version(client: AsyncClient) -> None:
    response = await client.get("/about")

    assert response.status_code == 200
    assert "Über eBauteileFuchs" in response.text
    assert "0.1.0" in response.text
