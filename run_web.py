"""Convenience launcher for the web dashboard during development.

    python run_web.py            # http://127.0.0.1:5000

For production use a real WSGI server with ``wsgi:app`` instead.
"""

from hostel_management.config import get_config
from hostel_management.web import app

if __name__ == "__main__":
    cfg = get_config()
    app.run(host="127.0.0.1", port=5000, debug=cfg.debug)
