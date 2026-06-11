"""WSGI entry point for production servers (gunicorn, waitress, etc.).

Example:
    gunicorn wsgi:app           # Linux/macOS
    waitress-serve --port 8000 wsgi:app   # Windows
"""

from hostel_management.web import app

if __name__ == "__main__":
    app.run()
