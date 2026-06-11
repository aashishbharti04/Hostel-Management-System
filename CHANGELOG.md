# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-06-11

A complete transformation from a single-file console script into a production-ready,
open-source application. **All original features are preserved.**

### Added
- **Web dashboard** (Flask): responsive UI with dark/light mode, dashboard statistics,
  full student CRUD, fee management, and live search.
- **JSON REST API** (`/api/...`) and a `/healthz` health-check endpoint.
- **Layered architecture**: `config` → `database` → `repository` → `services` →
  (`cli` / `web`), with shared models and validation.
- **SQLite backend** as a zero-config default, alongside the existing MySQL support.
- **Test suite** (pytest) covering models, services, the database layer, and the web app.
- **Tooling & CI**: ruff linting, GitHub Actions (build, lint, test, deploy checks).
- **Open-source scaffolding**: README, LICENSE (MIT), CONTRIBUTING, CODE_OF_CONDUCT,
  SECURITY, issue/PR templates, `.env.example`, and full `docs/`.
- Accessibility (ARIA, skip link, focus styles, reduced-motion), SEO meta tags, and a
  professional site footer with contact and social links.

### Changed
- The console menu now loops until you quit, validates input, and handles errors
  gracefully instead of crashing.
- Configuration moved to environment variables — no more hardcoded credentials.

### Fixed
- **Critical:** eliminated SQL injection by parameterising every query.
- **Critical:** removed the unconditional fee-insertion side effect that ran on startup.
- Fixed `IndexError` crashes when looking up a non-existent roll number/department.

### Security
- Removed committed database credentials.
- Added CSRF protection on all mutating web routes and relied on Jinja2 autoescaping
  to mitigate XSS.

## [1.0.0] - 2025-05-29

### Added
- Initial single-file console Hostel Management System (`6081.program.py`) with MySQL.
