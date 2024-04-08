from server.config import ROOT_PREFIX, CONFIG
import pytest

@pytest.mark.usefixtures("testapp")
@pytest.mark.dependency(depends=["patient_test.py::test_signup"])
def test_login(testapp):
    response = testapp.post(ROOT_PREFIX+"/auth/login/obtaintoken",
                           json={"username": "string", "password": "string"})
    
    assert response.status_code == 200
    assert "auth_token" in response.json()
    assert "refresh_token" in response.json()
    # assert response is a valid jwt token
