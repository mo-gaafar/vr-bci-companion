# signup patient

# Path: tests/patient_test.py

import pytest
from server.config import ROOT_PREFIX
from datetime import datetime


@pytest.mark.usefixtures("testapp")
def test_signup(testapp):
    data = {
        "username": "string",
        "password": "string",
        "email": "string@test.com",
        "phone": "string",
        "first_name": "string",
        "last_name": "string",
        "date_of_birth": "2024-04-09T00:39:17.014880Z",
        "medical_history": "string",
        "rehabilitation_program": "string",
        "diagnosis": "string"
    }
    # json = patient.model_dump_json()
    response = testapp.post(ROOT_PREFIX+"/patient/signup", json=data)
    if response.status_code == 400:
        assert response.json() == {
            'details': 'User already exists', 'message': 'Data validation error'}
    else:
        assert response.status_code == 201





