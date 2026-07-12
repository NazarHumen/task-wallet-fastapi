# TaskWallet API

A REST API for a task marketplace with a built-in wallet. Built on FastAPI +
SQLAlchemy. Managers publish paid tasks and escrow the reward from their
balance; executors complete tasks and get paid. Every balance change is
recorded in an append-only transaction ledger.

## Features

- JWT authentication with access + rotating refresh tokens; passwords hashed
  with Argon2 (`pwdlib`)
- Role-based access: `manager` (publishes and funds tasks) and `executor`
  (completes tasks and earns rewards)
- Wallet per user with available `balance` and `reserved_balance`
- Task lifecycle (`open`, `in_progress`, `submitted`, `completed`,
  `cancelled`): manager creates and reserves the reward, executor assigns,
  submits or abandons, manager approves (pays out) or cancels (refunds)
- Reward escrow: creating a task moves the reward from the manager's balance
  into reserved; approval releases it to the executor, cancellation refunds it
- Tags: CRUD and many-to-many tagging of tasks, with search and filtering
- Transaction ledger: append-only history of every available-balance change,
  with signed amounts, a `balance_after` snapshot, and an optional task link
- Self-service wallet: managers deposit funds, any user can withdraw
- Admin panel for all models via SQLAdmin
- OpenAPI schema and Swagger UI at `/docs`
- Pagination and filtering on list endpoints
- Config via `.env` (`pydantic-settings`), PostgreSQL as the database

## Tech Stack

- Python 3.12+
- FastAPI 0.138
- SQLAlchemy 2.0
- Alembic (migrations)
- Pydantic 2 / pydantic-settings
- PyJWT and pwdlib (Argon2)
- SQLAdmin (admin panel)
- PostgreSQL (psycopg2)
- Uvicorn (ASGI server)

## Installation

Requires Python 3.12+ and a running PostgreSQL instance.

```bash
git clone https://github.com/example.git
cd taskwallet

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS

pip install -r requirements.txt

cp .env.example .env
# fill in DATABASE_URL and JWT_SECRET_KEY
```

Create the database referenced by `DATABASE_URL`, then apply migrations:

```bash
alembic upgrade head
```

Run the development server:

```bash
uvicorn src.main:app --reload
```

The API will be available at http://127.0.0.1:8000/. The root path redirects
to the Swagger UI at http://127.0.0.1:8000/docs, and the admin panel is at
http://127.0.0.1:8000/admin.

## Project Structure

```
src/
  main.py           FastAPI app and router registration
  admin_panel.py    SQLAdmin setup
  auth/             JWT auth, users, roles, refresh tokens
  tasks/            Task lifecycle and reward escrow
  tags/             Tag CRUD and task tagging
  transactions/     Wallet ledger, deposit and withdraw
  db/               Engine, session, and settings
alembic/            Database migrations
```

## Environment Variables

Configured via `.env` (not committed). See `.env.example` for the template.

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL URL, e.g. `postgresql+psycopg2://user:pass@localhost:5432/taskwallet_db`. |
| `JWT_SECRET_KEY` | Secret for signing JWTs. Generate a new one for production. |
| `JWT_ALGORITHM` | JWT signing algorithm, e.g. `HS256`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime, in minutes. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime, in days. |

## Database Migrations

The project uses Alembic. Models are imported in `alembic/env.py` for
autogenerate support.

```bash
# apply all migrations
alembic upgrade head

# create a new migration after changing models
alembic revision --autogenerate -m "describe change"
```

## Code Style

The project uses **ruff** for linting and import sorting. Config lives in
`pyproject.toml` (line length 79).

```bash
# lint
ruff check src

# auto-fix
ruff check src --fix
```
