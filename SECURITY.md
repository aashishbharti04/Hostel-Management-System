# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 2.x     | ✅        |
| 1.x     | ❌        |

## Reporting a Vulnerability

We take security seriously. **Please do not report security vulnerabilities through public
GitHub issues.**

Instead, email **aashish@marketdoctorsonline.com** with:

- A description of the vulnerability and its impact
- Steps to reproduce (proof of concept if possible)
- Any suggested remediation

You can expect an acknowledgement within **72 hours** and a more detailed response
indicating next steps. We will keep you informed as we work on a fix and will credit you
(if you wish) once the issue is resolved.

## Security Measures in This Project

- **SQL injection:** all database access uses parameterised queries (see
  `hostel_management/database.py`). A regression test enforces this.
- **XSS:** Jinja2 autoescaping is enabled for all templates.
- **CSRF:** all state-changing web routes require a per-session CSRF token.
- **Secrets:** no credentials are committed; configuration is read from environment
  variables, and `.env` is git-ignored.
- **Input validation:** centralised in the model/service layer for both the CLI and web.

## Hardening Checklist for Deployments

- [ ] Set a strong, random `HMS_SECRET_KEY`
- [ ] Keep `HMS_DEBUG=false`
- [ ] Change `HMS_ADMIN_PASSWORD` from its default
- [ ] Serve over HTTPS behind a reverse proxy
- [ ] Use least-privilege database credentials
