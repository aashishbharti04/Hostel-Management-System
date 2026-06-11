"""Database access layer.

This module provides a thin abstraction over the two supported backends —
SQLite (the zero-config default) and MySQL — behind a single :class:`Database`
class. Crucially, **every** query is parameterised: callers pass values
separately from the SQL text, which closes the SQL-injection hole that existed
in the original script.

Queries are written with ``?`` placeholders (SQLite style). For MySQL the
placeholders are translated to ``%s`` automatically, so the rest of the code
base never needs to care which backend is active.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Iterator, Sequence
from contextlib import contextmanager
from typing import Any

from .config import Config, get_config

# Schema is intentionally backend-agnostic SQL. ``AUTOINCREMENT`` semantics are
# not required here because roll numbers and departments are natural keys.
SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS fees (
        department VARCHAR(50) PRIMARY KEY,
        amount     INTEGER NOT NULL CHECK (amount >= 0)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS students (
        roll_no  INTEGER PRIMARY KEY,
        name     VARCHAR(100) NOT NULL,
        address  VARCHAR(200) NOT NULL,
        room_no  INTEGER NOT NULL,
        dept     VARCHAR(50) NOT NULL,
        fees     INTEGER NOT NULL CHECK (fees >= 0),
        balance  INTEGER NOT NULL DEFAULT 0
    )
    """,
)


class Database:
    """Backend-agnostic database wrapper.

    The object is a lightweight connection holder. Use :meth:`cursor` for a
    managed cursor, or the higher-level :meth:`execute` / :meth:`query` helpers.
    """

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or get_config()
        self._paramstyle = "qmark" if self.config.db_backend == "sqlite" else "format"
        self._conn = self._connect()
        self.init_schema()

    # -- connection management ------------------------------------------------
    def _connect(self) -> Any:
        if self.config.db_backend == "sqlite":
            conn = sqlite3.connect(self.config.sqlite_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            return conn

        # MySQL: imported lazily so SQLite-only users need not install the driver.
        import mysql.connector as mysql  # type: ignore

        m = self.config.mysql
        return mysql.connect(
            host=m.host,
            port=m.port,
            user=m.user,
            password=m.password,
            database=m.database,
            autocommit=False,
        )

    def init_schema(self) -> None:
        """Create tables if they do not yet exist (idempotent)."""
        with self.cursor() as cur:
            for statement in SCHEMA_STATEMENTS:
                cur.execute(statement)
        self._conn.commit()

    def _translate(self, sql: str) -> str:
        """Translate ``?`` placeholders to the active backend's paramstyle."""
        if self._paramstyle == "qmark":
            return sql
        return sql.replace("?", "%s")

    @contextmanager
    def cursor(self) -> Iterator[Any]:
        """Yield a cursor and always close it."""
        cur = self._conn.cursor()
        try:
            yield cur
        finally:
            cur.close()

    # -- high level helpers ---------------------------------------------------
    def execute(self, sql: str, params: Sequence[Any] | None = None) -> int:
        """Run a write statement, commit, and return the affected row count."""
        with self.cursor() as cur:
            cur.execute(self._translate(sql), tuple(params or ()))
            rowcount = cur.rowcount
        self._conn.commit()
        return rowcount

    def query_one(self, sql: str, params: Sequence[Any] | None = None) -> dict[str, Any] | None:
        """Return the first row as a dict, or ``None``."""
        rows = self.query(sql, params)
        return rows[0] if rows else None

    def query(self, sql: str, params: Sequence[Any] | None = None) -> list[dict[str, Any]]:
        """Return all rows as a list of dicts (backend-agnostic)."""
        with self.cursor() as cur:
            cur.execute(self._translate(sql), tuple(params or ()))
            columns = [d[0] for d in cur.description] if cur.description else []
            rows: Iterable[Any] = cur.fetchall()
            return [self._row_to_dict(row, columns) for row in rows]

    @staticmethod
    def _row_to_dict(row: Any, columns: list[str]) -> dict[str, Any]:
        if isinstance(row, sqlite3.Row):
            return {key: row[key] for key in row.keys()}
        return dict(zip(columns, row, strict=False))

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:  # pragma: no cover - best-effort cleanup.
            pass

    def __enter__(self) -> Database:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
