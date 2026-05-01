import pytest
from httpx import AsyncClient, ASGITransport
from typing import AsyncGenerator

from app.main import app

# Ensure pytest-asyncio uses asyncio backend
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    # Use ASGITransport to test the FastAPI app without a real server
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
