# Contributing to Hostel Management System

First off — thank you for taking the time to contribute! 🎉 This project is open for
educational, learning, and community contributions, and we welcome issues and pull
requests of all sizes.

## Code of Conduct

By participating, you agree to uphold our [Code of Conduct](CODE_OF_CONDUCT.md).

## Ways to Contribute

- 🐛 **Report bugs** using the bug report template
- 💡 **Suggest features** using the feature request template
- 📝 **Improve documentation**
- 🔧 **Submit code** via pull requests

## Development Setup

```bash
git clone https://github.com/aashishbharti04/Hostel-Management-System.git
cd Hostel-Management-System

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements-dev.txt
cp .env.example .env             # Windows: copy .env.example .env
python -m hostel_management.seed
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for more detail.

## Making Changes

1. **Branch** from `main`:
   ```bash
   git checkout -b feat/short-description    # or fix/...
   ```
2. **Code** following the existing style. Keep changes focused.
3. **Test** your change:
   ```bash
   ruff check .
   ruff format --check .
   pytest
   ```
4. **Commit** with a clear, conventional message:
   ```
   feat: add room availability report
   fix: prevent negative balance on admission
   docs: clarify MySQL setup
   ```
5. **Push** and open a **Pull Request** using the template. Link any related issues.

## Pull Request Checklist

- [ ] Code is linted (`ruff check .`) and formatted
- [ ] Tests pass (`pytest`) and new behavior is covered
- [ ] Documentation updated if behavior changed
- [ ] No secrets, credentials, or local data committed

## Coding Guidelines

- Target **Python 3.10+** and keep type hints accurate.
- Put business rules in `services.py` / `models.py`, **not** in the CLI or web routes.
- **Never** build SQL by string concatenation — always use parameterised queries.
- Prefer small, pure functions and clear names over comments.

## Reporting Security Issues

Please do **not** open public issues for vulnerabilities. See [SECURITY.md](SECURITY.md).

---

Thanks again — happy hacking! 💜
