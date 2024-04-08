import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def testapp():
    from server.main import app
    yield app

from server.config import ROOT_PREFIX

def test_root(testapp):
    client = TestClient(testapp)
    response = client.get(ROOT_PREFIX+"/healthcheck")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
