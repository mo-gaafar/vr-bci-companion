import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def testapp():
    from server.main import app
    yield app


def test_root(testapp):
    client = TestClient(testapp)
    response = client.get("/")
    assert response.status_code == 200
    assert response.text == "Hello, world!"
