"""Flask application factory for the web dashboard.

Using the application-factory pattern keeps configuration explicit, makes the
app trivial to test, and avoids import-time side effects.
"""

from __future__ import annotations

from flask import Flask, render_template

from ..config import get_config
from .routes import register_routes


def create_app() -> Flask:
    """Build and configure the Flask application."""
    config = get_config()
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.update(
        SECRET_KEY=config.secret_key,
        JSON_SORT_KEYS=False,
        TEMPLATES_AUTO_RELOAD=config.debug,
    )

    register_routes(app)
    _register_error_handlers(app)
    return app


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(_err):  # type: ignore[no-untyped-def]
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(_err):  # type: ignore[no-untyped-def]
        return render_template("errors/500.html"), 500


# Convenience for `flask --app hostel_management.web run` and gunicorn.
app = create_app()
