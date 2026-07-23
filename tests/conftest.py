import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session", autouse=True)
def seed_test_user() -> None:
    """Create the test account through the public API, not a storage fixture."""
    client = TestClient(app)
    response = client.post(
        "/api/auth/register",
        json={"email": "user@example.com", "password": "Password123!"},
    )
    assert response.status_code in {201, 409}
