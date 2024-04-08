# from fastapi.testclient import TestClient
# # Replace 'your_project.main' with your app location
# from src.main import app

# import os

# # fix relative import path so that src is the root
# os.chdir(os.path.dirname("src"))
# client = TestClient(app)


# def test_login_success():
#     response = client.post("/login/obtaintoken", json={
#         "username": "string",
#         "password": "string"
#     })
#     assert response.status_code == 200
#     assert response.json()["token_type"] == "bearer"  # Assuming JWT tokens


# def test_login_failure():
#     response = client.post("/login", json={
#         "username": "invalid",
#         "password": "wrong"
#     })
#     assert response.status_code == 401  # Or your specific error code
