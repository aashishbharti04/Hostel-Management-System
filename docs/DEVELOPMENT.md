# Development Setup

## Prerequisites

- Python **3.10+**
- Git

## Getting started

```bash
git clone https://github.com/aashishbharti04/Hostel-Management-System.git
cd Hostel-Management-System

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements-dev.txt
cp .env.example .env             # Windows: copy .env.example .env
```

## Seed sample data

```bash
python -m hostel_management.seed
```

This creates `hostel.db` (SQLite) with default fees and five sample students.

## Run the app

```bash
python run_web.py    # web dashboard at http://127.0.0.1:5000
python run_cli.py    # console interface
```

Enable live reload while editing templates by setting `HMS_DEBUG=true` in `.env`.

## Running tests

```bash
pytest                                   # run all tests
pytest -v                                # verbose
pytest --cov=hostel_management           # with coverage
pytest tests/test_services.py::test_stats  # a single test
```

Each test uses an isolated temporary SQLite database, so tests never touch your dev data.

## Linting & formatting

```bash
ruff check .            # lint
ruff check . --fix      # auto-fix
ruff format .           # format
ruff format --check .   # verify formatting (what CI runs)
```

## Project conventions

- **Business rules** belong in `services.py` / `models.py` — never in the CLI or routes.
- **Never** concatenate SQL. Use parameterised queries via the `Database` helpers.
- Keep functions small and prefer descriptive names over comments.
- Add or update tests for any behavior change.
- Match the existing code style; CI enforces `ruff check` and `ruff format --check`.

## Switching to MySQL locally

```bash
# .env
HMS_DB_BACKEND=mysql
MYSQL_USER=root
MYSQL_PASSWORD=yourpassword
MYSQL_DATABASE=hostel_management
```

```bash
pip install "mysql-connector-python>=8.3"
# In MySQL: CREATE DATABASE hostel_management;
python -m hostel_management.seed
```

## Continuous Integration

Every push and pull request runs `.github/workflows/ci.yml`:

1. **Lint** — `ruff check` + `ruff format --check`
2. **Test** — `pytest` across Python 3.10/3.11/3.12
3. **Build** — `python -m build`
4. **Deploy checks** — boots the app and verifies key endpoints respond

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `ModuleNotFoundError: flask` | Activate the venv and `pip install -r requirements-dev.txt` |
| Web shows stale templates | Set `HMS_DEBUG=true` or restart the server |
| Want a clean DB | Delete `hostel.db` and re-run the seeder |
