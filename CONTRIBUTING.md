# Contributing to Converge AI

Thank you for contributing! Please read this guide before you write a single line of code.

---

## Branching Strategy (Git Flow)

We follow the **Git Flow** branching model used by production teams at companies like Google, Meta, and Netflix.

```
main          ── Production-ready. Never push directly.
  │
  └─ develop  ── Integration. All feature work lands here first via PR.
       │
       ├─ feature/whatsapp-improvements  ── Your work
       ├─ feature/add-memory-search
       └─ hotfix/fix-auth-token          ── Critical fix, branches from main
```

---

## Workflow – Step by Step

### 1. Clone and Set Up
```bash
git clone https://github.com/YOUR_ORG/Converge-AI.git
cd Converge-AI

# Always start from develop, not main
git checkout develop
git pull origin develop
```

### 2. Create Your Feature Branch
Always create your branch **from `develop`**, never from `main`:
```bash
# Convention: feature/<short-description>
git checkout -b feature/add-gmail-attachment-support
```

### 3. Write Code + Commit
Use clear, semantic commit messages:
```bash
git add .
git commit -m "feat(gmail): add attachment download support"
```

**Commit Message Convention** (Conventional Commits standard):
| Prefix | When to use |
|--------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Code restructuring, no feature change |
| `test` | Add/modify tests |
| `chore` | Tooling, CI, config changes |

### 4. Push and Open a PR → `develop`
```bash
git push origin feature/add-gmail-attachment-support
```
On GitHub, open a **Pull Request** targeting `develop` (not `main`).

The CI pipeline will automatically:
- Run the **Ruff** linter
- Check code formatting
- Run smoke import tests

Your PR **cannot be merged** until CI passes and at least **1 reviewer** approves.

### 5. Maintainer Merges `develop → main` (Release)
Only the maintainer performs releases. This is done by opening a PR from `develop` → `main`.

This PR represents a **production release** and triggers:
- Full CI gate (must pass)
- Automatic deployment to AWS EC2 production on merge ✅

---

## Hotfix Workflow (For Critical Production Bugs)

If there is an urgent bug in production:
```bash
# Branch from main directly
git checkout main
git pull origin main
git checkout -b hotfix/fix-whatsapp-loop

# ... fix the bug ...

git commit -m "fix(whatsapp): prevent message echo loop"
git push origin hotfix/fix-whatsapp-loop
```
Open a PR targeting **`main`** (not develop). After merging, also merge `main` back into `develop` to keep them in sync.

---

## Local Development Setup

```bash
# 1. Create .env from the example
cp .env.example .env
# Fill in GEMINI_API_KEY and SLACK_* tokens

# 2. Run locally with Docker
docker compose up --build

# 3. View WhatsApp QR Code (if enabled)
# Open: http://localhost:8000/webhooks/whatsapp/qr
```

---

## Code Style

We use **Ruff** for linting and formatting. Run it locally before pushing:
```bash
pip install ruff
ruff check src/       # Lint
ruff format src/      # Auto-format
```
