# Sales Service — FIAP Vehicle Resale Platform

Microservice responsible for the vehicle sale flow: sale initiation, payment webhook processing, and sold vehicle listing.

## Stack

- Python 3.11+ · FastAPI · SQLAlchemy (async) · Alembic · PostgreSQL · httpx

## Prerequisites

- Python 3.11+
- Docker + Docker Compose
- `kind` CLI (optional — CI uses it for k8s simulation)

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

## Pre-commit Hooks (required once per clone)

```bash
pip install pre-commit
pre-commit install                        # lint/format hooks
pre-commit install --hook-type commit-msg # conventional commits hook
```

## Running Locally

```bash
docker compose up --build -d
```

Service available at `http://localhost:8001`. API docs at `http://localhost:8001/docs`.

## Database Migrations

```bash
# Apply migrations
PYTHONPATH=src alembic upgrade head

# Generate migration after model changes
PYTHONPATH=src alembic revision --autogenerate -m "description"

# Rollback one step
PYTHONPATH=src alembic downgrade -1
```

## Running Tests

```bash
cd src
PYTHONPATH=src pytest
```

## Generating a JWT Token for Manual Testing

```bash
python3 -c "
from jose import jwt
import datetime
token = jwt.encode(
    {'sub': 'user@test.com', 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
    'changeme',
    algorithm='HS256'
)
print(token)
"
```

Use the token in requests:
```bash
curl -H "Authorization: Bearer <TOKEN>" http://localhost:8001/sales/sold
```

## Pre-commit Hooks

Validates formatting (black, ruff) and commit messages (Conventional Commits) before each `git commit`.

Commit message format: `type(scope): description` — e.g. `feat(sales): add sale initiation endpoint`
