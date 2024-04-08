# This file is used to define fixtures that can be used in multiple test files.
import logging
from server.config import CONFIG
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def testapp():
    from server.main import app
    # force config var to be test
    from server.config import CONFIG
    CONFIG.PRODUCTION = False
    app = TestClient(app)

    yield app


logging.basicConfig(level=logging.INFO)

@pytest.fixture(scope="session")
def clear_test_db():
    from server.database import conn
    # make sure its the test db
    if CONFIG.PRODUCTION:
        raise Exception("Cannot clear production db")
    conn.drop_database(CONFIG.MONGO_DB_TEST)
