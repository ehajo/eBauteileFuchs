import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_installable_shell_and_offline_page_do_not_cache_writes(
    client: AsyncClient,
) -> None:
    home = await client.get("/")
    assert 'rel="manifest"' in home.text
    assert 'src="http://testserver/static/js/pwa.js?v=' in home.text
    assert 'href="/search"' in home.text
    assert 'href="/connection"' in home.text

    manifest = await client.get("/static/manifest.webmanifest")
    assert manifest.status_code == 200
    assert manifest.json()["display"] == "standalone"
    assert manifest.json()["start_url"] == "/"
    assert {item["sizes"] for item in manifest.json()["icons"]} == {
        "192x192",
        "512x512",
    }
    assert (await client.get("/static/branding/app-icon-192.svg")).status_code == 200
    assert (await client.get("/static/branding/app-icon-512.svg")).status_code == 200

    worker = await client.get("/service-worker.js")
    assert worker.status_code == 200
    assert worker.headers["service-worker-allowed"] == "/"
    assert 'request.method !== "GET"' in worker.text
    assert "api/v1" not in worker.text
    assert "inventory/stock" not in worker.text
    assert "/static/vendor/zxing-wasm/reader.js" in worker.text
    assert "/static/vendor/zxing-wasm/zxing_reader.wasm" in worker.text

    quick_booking = await client.get("/static/js/quick-booking.js")
    assert quick_booking.status_code == 200
    assert "submittedAction.name = submitter.name" in quick_booking.text
    assert "submittedAction.value = submitter.value" in quick_booking.text
    assert quick_booking.text.index(
        "form.append(submittedAction)"
    ) < quick_booking.text.index("submitter.disabled = true")

    offline = await client.get("/offline")
    assert offline.status_code == 200
    assert "nicht offline gespeichert oder synchronisiert" in offline.text
