"""Application configuration.

Configuration is read from environment variables so that no secret ever lives
in source control (see ``.env.example`` for the full list). A local ``.env``
file is loaded automatically when ``python-dotenv`` is installed, which keeps
local development friction-free without compromising production secrets.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:  # python-dotenv is an optional convenience dependency.
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv is optional.
    pass


# Repository root, used to resolve the default SQLite database location.
BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(name: str, default: bool = False) -> bool:
    """Parse a truthy environment variable."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class MySQLConfig:
    """Connection settings for the optional MySQL backend."""

    host: str = field(default_factory=lambda: os.getenv("MYSQL_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("MYSQL_PORT", "3306")))
    user: str = field(default_factory=lambda: os.getenv("MYSQL_USER", "root"))
    password: str = field(default_factory=lambda: os.getenv("MYSQL_PASSWORD", ""))
    database: str = field(default_factory=lambda: os.getenv("MYSQL_DATABASE", "hostel_management"))


@dataclass(frozen=True)
class Config:
    """Top-level application configuration.

    Attributes:
        db_backend: ``"sqlite"`` (default, zero-config) or ``"mysql"``.
        sqlite_path: Filesystem path to the SQLite database file.
        mysql: MySQL connection settings (used only when ``db_backend`` is mysql).
        secret_key: Flask session secret. MUST be overridden in production.
        admin_password: Password gating administrative ("Authorities only") actions.
    """

    db_backend: str = field(default_factory=lambda: os.getenv("HMS_DB_BACKEND", "sqlite").lower())
    sqlite_path: str = field(
        default_factory=lambda: os.getenv("HMS_SQLITE_PATH", str(BASE_DIR / "hostel.db"))
    )
    mysql: MySQLConfig = field(default_factory=MySQLConfig)
    secret_key: str = field(
        default_factory=lambda: os.getenv("HMS_SECRET_KEY", "dev-secret-change-me")
    )
    admin_password: str = field(default_factory=lambda: os.getenv("HMS_ADMIN_PASSWORD", "admin"))
    debug: bool = field(default_factory=lambda: _env_bool("HMS_DEBUG", False))

    def validate(self) -> None:
        """Fail fast on obviously invalid configuration."""
        if self.db_backend not in {"sqlite", "mysql"}:
            raise ValueError(
                f"Unsupported HMS_DB_BACKEND={self.db_backend!r}; expected 'sqlite' or 'mysql'."
            )


def get_config() -> Config:
    """Build and validate the active configuration."""
    cfg = Config()
    cfg.validate()
    return cfg
