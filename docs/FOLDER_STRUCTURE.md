# Folder Structure

```
Hostel-Management-System/
├── hostel_management/            # Core application package
│   ├── __init__.py               # Package metadata (__version__)
│   ├── config.py                 # Env-based configuration
│   ├── database.py               # SQLite/MySQL abstraction (parameterised SQL)
│   ├── models.py                 # Dataclasses + validation (Student, Fee)
│   ├── repository.py             # Data access (CRUD repositories)
│   ├── services.py               # Business logic (shared by CLI + Web)
│   ├── seed.py                   # Sample-data seeder
│   ├── cli.py                    # Command-line interface (the modern console app)
│   └── web/                      # Flask web dashboard
│       ├── __init__.py           # Application factory (create_app)
│       ├── routes.py             # Page routes + JSON API + CSRF
│       ├── templates/            # Jinja2 templates
│       │   ├── base.html         # Layout: head/SEO, nav, footer, theme
│       │   ├── dashboard.html    # Stats + recent students
│       │   ├── fees.html         # Fee schedule management
│       │   ├── students/
│       │   │   ├── list.html     # Student table + search
│       │   │   └── form.html     # Admission / edit form
│       │   └── errors/
│       │       ├── 404.html
│       │       └── 500.html
│       └── static/
│           ├── css/styles.css    # Design system (light/dark, responsive)
│           ├── js/main.js        # Theme toggle, flash, confirm dialogs
│           └── img/favicon.svg
│
├── tests/                        # Pytest suite
│   ├── conftest.py               # Fixtures (isolated SQLite per test)
│   ├── test_models.py            # Validation tests
│   ├── test_services.py          # Service/repository/DB integration tests
│   └── test_web.py               # Route + API + CSRF end-to-end tests
│
├── docs/                         # Documentation
│   ├── ARCHITECTURE.md
│   ├── FOLDER_STRUCTURE.md
│   ├── API.md
│   ├── DEPLOYMENT.md
│   ├── DEVELOPMENT.md
│   ├── screenshots/              # README screenshots
│   └── assets/                   # Original project report (archived)
│
├── .github/                      # GitHub configuration
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── config.yml
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/ci.yml          # Lint · Test · Build · Deploy checks
│
├── run_cli.py                    # Convenience launcher for the CLI
├── run_web.py                    # Convenience launcher for the dev web server
├── wsgi.py                       # Production WSGI entry point
├── pyproject.toml                # Packaging, scripts, ruff & pytest config
├── requirements.txt              # Runtime dependencies
├── requirements-dev.txt          # Dev/test/lint dependencies
├── .env.example                  # Template environment configuration
├── .gitignore
├── README.md
├── LICENSE                       # MIT
├── CONTRIBUTING.md
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
└── SECURITY.md
```

## Where to make changes

| I want to… | Edit… |
| --- | --- |
| Change a business rule | `hostel_management/services.py` or `models.py` |
| Add a database query | `hostel_management/repository.py` |
| Add a web page or endpoint | `hostel_management/web/routes.py` (+ a template) |
| Change styling/theme | `hostel_management/web/static/css/styles.css` |
| Add a CLI menu action | `hostel_management/cli.py` |
| Add configuration | `hostel_management/config.py` and `.env.example` |
