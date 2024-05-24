from server.config import ROOT_PREFIX, CONFIG
import pytest


@pytest.mark.usefixtures("testapp")
@pytest.mark.dependency(depends=["patient_test.py::test_signup"])
def test_login(testapp):
    data = {
        "username": "string",
        "password": "string"
    }
    response = testapp.post(ROOT_PREFIX+"/auth/login/obtaintoken", json=data)
    assert response.status_code == 200
    assert "auth_token" in response.json()
    assert "refresh_token" in response.json()
    assert response.status_code == 200

    # return the token for the user
    return response.json()["auth_token"]


@pytest.mark.usefixtures("testapp")
def test_pairing(testapp):
    # api url
    headset_id = "string"
    url = ROOT_PREFIX+"/auth/headset/generateotp"
    url += f"?headset_id={headset_id}"  # headset id query parameter
    header = {"Authorization": "Bearer " + test_login(testapp)}

    # send get request to get the otp for pairing
    response = testapp.get(url, headers=header)
    # check if the response is successful
    assert response.status_code == 200
    otp = response.json()["otp"]

    # pair the headset with the otp by entering it on the website
    url = ROOT_PREFIX+"/auth/enterotp"
    response = testapp.post(url, json={"code": otp}, headers=header)
    assert response.status_code == 200

    return otp, headset_id


@pytest.mark.usefixtures("testapp")
def test_headset_token_login(testapp):
    otp, headset_id = test_pairing(testapp)
    data = {
        "otp": otp,
        "headset_id": headset_id
    }
    url = "/auth/headset/login/obtaintoken"
    url += f"?headset_id={headset_id}"  # headset id query parameter
    url += f"&otp={otp}"  # otp query parameter
    response = testapp.post(ROOT_PREFIX+url, json=data)
    assert response.status_code == 200
    assert "auth_token" in response.json()
    assert "refresh_token" in response.json()
