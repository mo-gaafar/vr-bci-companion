import httpx
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from ..main import app  

# Initialize the test client
client = TestClient(app)

# Test get_tickets_status endpoint
def test_get_tickets_status():
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=7)
    tenant_id = "your_tenant_id"

    response = client.get(
        "/status/tickets",
        headers={"tenant_id": tenant_id},
        params={"start_date": start_date, "end_date": end_date},
    )
    assert response.status_code == 200
    assert response.json()  # Verify the response body here

# Test get_checkin_histogram endpoint
def test_get_checkin_histogram():
    bin_minutes = 10
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=7)
    tenant_id = "your_tenant_id"

    response = client.get(
        "/checkin/histogram",
        headers={"tenant_id": tenant_id},
        params={"bin_minutes": bin_minutes, "start_date": start_date, "end_date": end_date},
    )
    assert response.status_code == 200
    assert response.json()  # Verify the response body here

# Test get_recent_scans endpoint
def test_get_recent_scans():
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=7)
    n_last = 10
    tenant_id = "your_tenant_id"

    response = client.get(
        "/scan/recent",
        headers={"tenant_id": tenant_id},
        params={"start_date": start_date, "end_date": end_date, "n_last": n_last},
    )
    assert response.status_code == 200
    assert response.json()  # Verify the response body here

# Run the tests
def run_tests():
    test_get_tickets_status()
    test_get_checkin_histogram()
    test_get_recent_scans()

# Run the test suite
if __name__ == "__main__":
    run_tests()
