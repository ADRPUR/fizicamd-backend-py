import os
import pytest

db_url = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
if not db_url:
    pytest.skip("DATABASE_URL or TEST_DATABASE_URL is not set", allow_module_level=True)
if os.getenv("TEST_DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.core.db import SessionLocal  # noqa: E402
from app.core.migrations import run_migrations  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    run_migrations()


@pytest.fixture()
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client():
    return TestClient(app)
