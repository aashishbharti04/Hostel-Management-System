# Deployment Guide

This guide covers running the web dashboard in production. The development server
(`python run_web.py`) is **not** suitable for production.

## 1. Prerequisites

- Python 3.10+
- A WSGI server (gunicorn on Linux/macOS, waitress on Windows)
- (Optional) MySQL if you don't want to use SQLite
- (Recommended) A reverse proxy (nginx/Caddy) terminating HTTPS

## 2. Environment

Create a `.env` (or set real environment variables) with **production** values:

```bash
HMS_DB_BACKEND=sqlite            # or mysql
HMS_SQLITE_PATH=/var/lib/hms/hostel.db
HMS_SECRET_KEY=<64-hex-random>   # python -c "import secrets;print(secrets.token_hex(32))"
HMS_ADMIN_PASSWORD=<strong-password>
HMS_DEBUG=false
```

For MySQL, also set `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`, and
create the database once: `CREATE DATABASE hostel_management;` (tables auto-create).

## 3. Install

```bash
pip install -r requirements.txt
# For MySQL: pip install "mysql-connector-python>=8.3"
```

## 4. Run with a WSGI server

### Linux / macOS (gunicorn)

```bash
pip install gunicorn
gunicorn wsgi:app --bind 0.0.0.0:8000 --workers 4
```

### Windows (waitress)

```powershell
pip install waitress
waitress-serve --port 8000 wsgi:app
```

## 5. Reverse proxy (nginx example)

```nginx
server {
    listen 443 ssl;
    server_name hms.example.com;

    ssl_certificate     /etc/letsencrypt/live/hms.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/hms.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 6. Docker (optional)

A minimal Dockerfile:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn
COPY . .
ENV HMS_DB_BACKEND=sqlite HMS_DEBUG=false
EXPOSE 8000
CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

```bash
docker build -t hostel-management .
docker run -p 8000:8000 -e HMS_SECRET_KEY=$(openssl rand -hex 32) hostel-management
```

## 7. Platform notes

- **Render / Railway / Fly.io:** set the start command to `gunicorn wsgi:app` and add the
  environment variables above. Use a persistent volume for the SQLite file or a managed
  MySQL instance.
- **Health checks:** point your platform's health check at `/healthz`.

## 8. Production checklist

- [ ] `HMS_SECRET_KEY` is strong and unique
- [ ] `HMS_DEBUG=false`
- [ ] `HMS_ADMIN_PASSWORD` changed from default
- [ ] HTTPS enabled at the proxy
- [ ] Database backups configured
- [ ] Least-privilege DB credentials
