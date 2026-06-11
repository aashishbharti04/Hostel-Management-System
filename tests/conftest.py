"""Shared pytest fixtures.

Each test runs against a fresh, isolated SQLite database created in a temporary
directory, so tests never touch real data and never interfere with each other.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hostel_management.config import Config
from hostel_management.database import Database
from hostel_management.services import HostelService


@pytest.fixture()
def db_path(tmp_path: Path) -> str:
    return str(tmp_path / "test.db")


@pytest.fixture()
def database(db_path: str, monkeypatch: pytest.MonkeyPatch) -> Database:
    monkeypatch.setenv("HMS_DB_BACKEND", "sqlite")
    monkeypatch.setenv("HMS_SQLITE_PATH", db_path)
    db = Database(Config())
    yield db
    db.close()


@pytest.fixture()
def service(database: Database) -> HostelService:
    svc = HostelService(database)
    yield svc


@pytest.fixture()
def client(db_path: str, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("HMS_DB_BACKEND", "sqlite")
    monkeypatch.setenv("HMS_SQLITE_PATH", db_path)
    monkeypatch.setenv("HMS_SECRET_KEY", "test-secret")
    from hostel_management.web import create_app

    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as c:
        yield c
