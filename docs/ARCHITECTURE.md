# Architecture

## Overview

The application follows a **layered architecture**. Each layer has a single responsibility
and depends only on the layer beneath it. The two front-ends (CLI and Web) sit on top of a
shared core, so business behavior is identical regardless of how you interact with the app.

```
┌─────────────────────┐     ┌─────────────────────┐
│   CLI (cli.py)      │     │  Web (web/ — Flask) │   ← Presentation
└──────────┬──────────┘     └──────────┬──────────┘
           │                           │
           └───────────┬───────────────┘
                       ▼
            ┌─────────────────────┐
            │  Services           │   ← Business logic / rules
            │  (services.py)      │
            └──────────┬──────────┘
                       ▼
            ┌─────────────────────┐
            │  Repositories       │   ← Data access (parameterised SQL)
            │  (repository.py)    │
            └──────────┬──────────┘
                       ▼
            ┌─────────────────────┐
            │  Database           │   ← SQLite / MySQL abstraction
            │  (database.py)      │
            └─────────────────────┘

  Cross-cutting: config.py (env config) · models.py (data + validation)
```

## Layers

### 1. Configuration (`config.py`)
Reads all settings from environment variables (with a `.env` convenience loader). No secret
ever lives in source. Exposes an immutable `Config` dataclass and `get_config()`.

### 2. Database (`database.py`)
A thin, backend-agnostic wrapper over SQLite (default) and MySQL. **Every query is
parameterised** — values are passed separately from SQL text. Queries are written with `?`
placeholders and translated to `%s` for MySQL automatically. Also creates the schema
idempotently on startup.

### 3. Models (`models.py`)
Typed `dataclasses` (`Student`, `Fee`) plus a `ValidationError`. Validation rules live here
as the **single source of truth** used by both front-ends. `DEPARTMENTS` is defined once.

### 4. Repositories (`repository.py`)
Translate between models and database rows. Pure CRUD, no business rules — which makes them
easy to reason about and test.

### 5. Services (`services.py`)
The application's brain. Validates input, enforces rules (no duplicate roll numbers,
case-insensitive department lookups, seeding default fees), and orchestrates repositories.
**Both** the CLI and the web layer call only services.

### 6. Presentation
- **CLI (`cli.py`)** — a robust menu loop with validation and friendly errors.
- **Web (`web/`)** — a Flask app factory, Jinja2 templates, a CSS design system, and a
  small progressive-enhancement JS layer. Includes a JSON API and error pages.

## Key Design Decisions

| Decision | Rationale |
| --- | --- |
| Shared service layer | One place for business rules → CLI and Web never diverge. |
| SQLite default | Zero-config; anyone can run the project instantly. |
| `?`-placeholder translation | One SQL dialect in code; backend chosen at runtime. |
| App-factory pattern | Clean configuration and easy testing (no import-time side effects). |
| Request-scoped DB connections | Simple and safe for the app's scale; no shared mutable state. |
| Env-based config | Secrets stay out of source; 12-factor friendly. |

## Request Flow (Web example: admitting a student)

1. `POST /students/new` → `student_new()` route.
2. CSRF token verified; form parsed into a `Student` via `_student_from_form`.
3. `HostelService.admit_student()` validates and checks for duplicates.
4. `StudentRepository.add()` runs a parameterised `INSERT`.
5. `Database.execute()` commits and returns the row count.
6. A flash message is set and the user is redirected to the list.

## Security Architecture

See [SECURITY.md](../SECURITY.md). Highlights: parameterised SQL, Jinja2 autoescaping
(XSS), per-session CSRF tokens, env-based secrets, and centralised input validation.
