import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_health_reports_application_and_database(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "eBauteileFuchs",
        "version": "0.1.0",
        "database": "ok",
    }
