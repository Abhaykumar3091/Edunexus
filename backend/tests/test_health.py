import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """
    Test root endpoint returns application metadata.
    """
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "UniAssist AI"
    assert "version" in data
    assert "docs" in data


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """
    Test /api/v1/health endpoint confirms online status and healthy database.
    """
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert res_json["data"]["status"] == "online"
    assert res_json["data"]["database"] == "healthy"
    assert "services" in res_json["data"]
