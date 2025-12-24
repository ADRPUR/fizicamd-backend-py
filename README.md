# FizicaMD Backend (FastAPI)

FastAPI rewrite of the current backend, keeping the same endpoints and DB schema.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` from `.env.example`, then run:

```bash
uvicorn app.main:app --reload
```

## Docker

```bash
docker compose up --build
```

## Scripts

```bash
./scripts/run-dev.sh
./scripts/run-tests.sh
```

## Migrations
Migrations are idempotent SQL files in `migrations/` and are applied on startup.

## Tests
Install dev dependencies and set a DB connection:

```bash
pip install -r requirements-dev.txt
export TEST_DATABASE_URL=postgresql+psycopg://fizicamd:fizicamd@localhost:5432/fizicamd_test
```

Then run:

```bash
pytest -q
```

## Notes
- WebSocket metrics endpoint: `/ws/metrics?token=...`
- API base: `/api`
