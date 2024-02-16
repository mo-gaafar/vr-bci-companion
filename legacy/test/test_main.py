import pytest
from ..main import app
from fastapi.testclient import TestClient
from test_dashboard import test_get_tickets_status, test_get_checkin_histogram, test_get_recent_scans


# Initialize the test client
client = TestClient(app)

# Test cases go here...
test_get_checkin_histogram()
test_get_recent_scans()
test_get_tickets_status()

# Define a fixture to provide the test client

@pytest.fixture
def test_client():
    return client


# Run the tests using pytest
if __name__ == "__main__":
    # Run the tests

    pytest.main()
