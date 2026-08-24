from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from ebauteilefuchs.application.ports.supplier_cache import SupplierCacheEntry
from ebauteilefuchs.persistence.article_catalog import MOUSER_SUPPLIER


@pytest.mark.anyio
async def test_generic_supplier_cache_hit_expiry_and_clear(client: AsyncClient) -> None:
    cache = client._transport.app.state.supplier_cache
    now = datetime.now(UTC)
    entry = SupplierCacheEntry(
        supplier_id=MOUSER_SUPPLIER[0],
        query_type="synthetic-test",
        query_normalized="abc",
        adapter_version="fake-v1",
        response_json='{"synthetic":true}',
        status="success",
        created_at=now,
        expires_at=now + timedelta(minutes=5),
    )
    cache.put(entry)
    assert (
        cache.get(
            entry.supplier_id,
            entry.query_type,
            entry.query_normalized,
            entry.adapter_version,
            now=now,
        )
        == entry
    )
    assert (
        cache.get(
            entry.supplier_id,
            entry.query_type,
            entry.query_normalized,
            entry.adapter_version,
            now=now + timedelta(minutes=6),
        )
        is None
    )
    cleared = await client.delete("/api/v1/suppliers/mouser/cache")
    assert cleared.status_code == 200
    assert cleared.json() == {"deleted": 1}
