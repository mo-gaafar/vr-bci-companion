from fastapi.testclient import TestClient
import pytest
from server.config import ROOT_PREFIX


@pytest.mark.usefixtures("testapp")
def test_root(testapp):
    response = testapp.get(ROOT_PREFIX+"/healthcheck")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
