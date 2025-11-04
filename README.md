# Car Rental Platform API

Backend service for a car-rental platform built with Flask, SQLAlchemy, Alembic, and PostgreSQL. The application is designed to run entirely inside Docker containers.

## Prerequisites

- Docker Desktop 4.27+ (or compatible Docker Engine) with Compose V2
- Make sure nothing else is bound to the host ports you want to use (defaults: API `5005`, Postgres `15432`)

## Environment Configuration

Update `.env` as needed; the defaults are:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=car-rental-platform-api
APP_PORT=5005
DB_HOST_PORT=15432
```

- `APP_PORT` controls which port the API exposes on the host.
- `DB_HOST_PORT` is the host-side PostgreSQL port. Change it if `5432` or `15432` conflicts with something else.

## First-Time Setup

These commands assume you just cloned the project (or removed the `migrations/` folder and want to rebuild it).

```bash
docker compose down -v                 # optional cleanup step
docker compose build
docker compose up -d db                # start Postgres first
docker compose run --rm api flask db init
docker compose run --rm api flask db migrate -m "initial schema"
docker compose run --rm api flask db upgrade
docker compose up -d                   # start the API + reattach the db
```

The API container runs `flask db upgrade` automatically on startup, so it stays in sync with the latest migrations.

## Working on the Schema Later

Whenever you change models:

```bash
docker compose run --rm api flask db migrate -m "describe change"
docker compose run --rm api flask db upgrade
```

The `migrations/` directory is mounted from the host, so Alembic revisions generated inside the container show up in your local workspace.

## Useful Commands

- Follow logs: `docker compose logs -f api`
- Rebuild images after dependency changes: `docker compose build`
- Run everything in the foreground (CTRL+C to stop): `docker compose up`
- Tear everything down but keep data: `docker compose down`
- Tear everything down and remove volumes (wipes Postgres data): `docker compose down -v`

## Connecting with DataGrip (or any SQL client)

Point your client at the host-mapped port:

- Host: `localhost`
- Port: value of `DB_HOST_PORT` (default `15432`)
- Database: `car-rental-platform-api`
- Username: `postgres`
- Password: `postgres`

If you change `DB_HOST_PORT` in `.env`, rebuild the stack or recreate the `db` service so Docker picks up the new mapping: `docker compose up -d db --force-recreate`.

