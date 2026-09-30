import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

def run_async(coro):
    return asyncio.run(coro)

def test_prometheus_metrics_endpoint():
    """Verify that the /metrics endpoint is exposed and responds with Prometheus text data."""
    async def _test():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/metrics")
            assert response.status_code == 200, "Metrics endpoint should return HTTP 200."
            assert "http_requests_total" in response.text or "process_cpu_seconds_total" in response.text, \
                "Response text should contain standard Prometheus metrics keys."

    run_async(_test())
