import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_home_page_contains_branding_and_no_external_assets(
    client: AsyncClient,
) -> None:
    response = await client.get("/")

    assert response.status_code == 200
    assert "Verpackungsbarcode scannen" in response.text
    assert 'data-scan-url="/suppliers/mouser?mode=barcode&amp;q="' in response.text
    assert 'capture="environment"' in response.text
    assert "Foto aufnehmen" in response.text
    assert "vendor/zxing-wasm/reader.js" in response.text
    assert response.text.index("vendor/zxing-wasm/reader.js") < response.text.index(
        "js/barcode-scanner.js"
    )
    assert "eBauteileFuchs" in response.text
    assert "Clever finden statt lange suchen." in response.text
    assert "eBauteileFuchs – ein Open-Source-Projekt von eHaJo" in response.text
    assert "fonts.googleapis.com" not in response.text
    assert "Fuchs-Maskottchen von eBauteileFuchs" in response.text
    assert "/static/branding/fuchs-maskottchen.png" in response.text


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
    assert ".search-bar__row--scanner input" in styles.text
    assert "grid-column: 1 / -1" in styles.text
