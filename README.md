# Car Rental Platform API

Car Rental Platform API is a role-aware backend for onboarding merchants with vehicle fleets and enabling end-users to discover, rent, and return cars in near real time. It is built with Flask, SQLAlchemy, Alembic, and PostgreSQL, and is meant to run entirely inside Docker containers for reproducible local development or lightweight deployment.

## Purpose

The service models two personas:

- **Merchants** manage fleets, publish inventory, and inspect rental performance.
- **Drivers (end-users)** browse available vehicles, start rentals, and return cars.

Authentication is cookie-based via Flask-Login, so once a user signs in, subsequent requests simply reuse the session cookie—making it easy for third parties to integrate through browsers, Postman, or curl.

## Architecture & Tech Stack

- Flask application factory with blueprints per domain (`auth`, `cars`, `rentals`, `core`).
- SQLAlchemy ORM models, Alembic migrations, and PostgreSQL storage.
- Flask-Login for session handling, bcrypt for password hashing, and role-based decorators to restrict endpoints.
- Docker Compose orchestrates the API container and PostgreSQL database; migrations run automatically on container start.

## Key Features

- Role-based authentication (standard users vs. merchants) with merchant-company onboarding.
- Merchant-facing CRUD for cars plus filtered pagination for large fleets.
- Public car discovery (`/cars` + `/cars/query-cars`) with make/model/year/price filters.
- Rental lifecycle management (start, return, historical records, fee calculation).
- Rich query endpoints for both renters and merchants to inspect rentals with pagination, fee filters, and date ranges.

## Domain Roles & Entities

| Entity / Role | Description |
| --- | --- |
| `User` | Base account with `email`, `name`, `surname`, hashed password, and `role`. |
| `Merchant` | One-to-one extension of `User` accounts with `role = merchant`, holding `company_name` and associated cars. |
| `Car` | Inventory item with `make`, `model`, `year`, `price_per_hour`, `status` (`available`/`rented`), linked to a merchant. |
| `Rental` | Represents a driver’s booking, captures rental & return timestamps and computes `total_fee`. |

## API Surface

Base URL defaults to `http://localhost:5005`. All authenticated routes rely on the Flask session cookie returned on login.

### Auth

| Method | Endpoint | Description | Auth |
| --- | --- | --- | --- |
| `POST` | `/auth/register` | Create user or merchant. Merchants must include `role=merchant` and `company_name`. | Public |
| `POST` | `/auth/login` | Email/password login. Stores a session cookie. | Public |
| `POST` | `/auth/logout` | Clears the session. | Logged-in |
| `GET` | `/auth/me` | Returns the current user profile and role. | Logged-in |

### Cars

| Method | Endpoint | Description | Role |
| --- | --- | --- | --- |
| `POST` | `/cars/create` | Merchant creates a car (make/model/year/price). | Merchant |
| `GET` | `/cars/my-cars` | List all cars that belong to the logged-in merchant. | Merchant |
| `PUT` | `/cars/<car_id>` | Update make/model/year/price/status if you own the car. | Merchant |
| `DELETE` | `/cars/<car_id>` | Delete a car (must not be rented). | Merchant |
| `GET` | `/cars/<car_id>` | Retrieve a single car (public). | Public |
| `GET` | `/cars/` | List all cars (public). | Public |
| `GET` | `/cars/query-cars` | Paginated discovery for available cars with filters (`make`, `model`, `year`, `min_price`, `max_price`, `merchant_id`). | Public |
| `GET` | `/cars/query-merchant-cars` | Merchant-only paginated listings with status & pricing filters. | Merchant |

### Rentals

| Method | Endpoint | Description | Role |
| --- | --- | --- | --- |
| `POST` | `/rentals/rent/<car_id>` | Start a rental. Fails if you already have an active rental or the car is unavailable. | User |
| `POST` | `/rentals/return` | Complete the active rental; calculates total fees using car hourly price. | User |
| `GET` | `/rentals/user/history` | List all rentals for the logged-in user. | User |
| `GET` | `/rentals/user/query` | Paginated rental history filters (status, fees, car details, date windows). | User |
| `GET` | `/rentals/merchant/history` | Rentals involving the merchant’s fleet. | Merchant |
| `GET` | `/rentals/merchant/query` | Merchant rental analytics with pagination plus `user_id`, `car_id`, `status`, fee & date filters. | Merchant |

## Prerequisites

- Docker Desktop 4.27+ (or compatible Docker Engine) with Compose V2.
- Ensure host ports are free (defaults: API `5005`, Postgres `15432`).

## Environment Configuration

Update `.env` (create it if it does not exist) with any overrides; defaults are:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=car-rental-platform-api
APP_PORT=5005
DB_HOST_PORT=15432
```

- `APP_PORT` controls which port the API exposes on the host.
- `DB_HOST_PORT` is the host-side PostgreSQL port. Change it if `5432` or `15432` conflicts with something else.

## Running the Stack

### Quick Start (fresh clone)

Because Alembic migrations already live in `migrations/`, you can boot the stack immediately after cloning:

```bash
docker compose build
docker compose up -d
```

The API container runs `flask db upgrade` on startup, so the database schema syncs automatically.

### First-Time Setup

Only use these commands if you intentionally removed the `migrations/` folder and need to recreate the migration history from scratch.

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

### Working on the Schema Later

Whenever you change models:

```bash
docker compose run --rm api flask db migrate -m "describe change"
docker compose run --rm api flask db upgrade
```

The `migrations/` directory is mounted from the host, so Alembic revisions generated inside the container show up in your local workspace.

### Useful Commands

- Follow logs: `docker compose logs -f api`
- Rebuild images after dependency changes: `docker compose build`
- Run everything in the foreground (CTRL+C to stop): `docker compose up`
- Tear everything down but keep data: `docker compose down`
- Tear everything down and remove volumes (wipes Postgres data): `docker compose down -v`

### Connecting with DataGrip (or any SQL client)

Point your client at the host-mapped port:

- Host: `localhost`
- Port: value of `DB_HOST_PORT` (default `15432`)
- Database: `car-rental-platform-api`
- Username: `postgres`
- Password: `postgres`

If you change `DB_HOST_PORT` in `.env`, rebuild the stack or recreate the `db` service so Docker picks up the new mapping: `docker compose up -d db --force-recreate`.

## Third-Party Usage Guide

Once the containers are running, any external consumer can interact with the API using cURL, Postman, Hoppscotch, or a browser (session cookies will be set by `/auth/login`). A typical flow:

1. **Start the stack**
   ```bash
   docker compose up -d
   ```
   API is now at `http://localhost:5005`.

2. **Register accounts**
   - Merchant (requires `role` + `company_name`):
     ```bash
     curl -X POST http://localhost:5005/auth/register \
       -H "Content-Type: application/json" \
       -d '{"email":"merchant@example.com","password":"Pass123!","name":"Mary","surname":"Merchant","role":"merchant","company_name":"Premium Cars"}'
     ```
   - Driver (default role is `user`, so omit `role`):
     ```bash
     curl -X POST http://localhost:5005/auth/register \
       -H "Content-Type: application/json" \
       -d '{"email":"driver@example.com","password":"Pass123!","name":"Dan","surname":"Driver"}'
     ```

3. **Authenticate and capture the session cookie**
   Flask-Login responds with a `Set-Cookie` header. Use `curl`’s cookie jar to persist it:
   ```bash
   curl -X POST http://localhost:5005/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"merchant@example.com","password":"Pass123!"}' \
     -c merchant-cookie.txt
   ```
   Subsequent merchant-only actions pass `-b merchant-cookie.txt`. Repeat the same for the driver (use a different cookie jar file).

4. **Merchant publishes inventory**
   ```bash
   curl -X POST http://localhost:5005/cars/create \
     -H "Content-Type: application/json" \
     -b merchant-cookie.txt \
     -d '{"make":"Tesla","model":"Model 3","year":2023,"price_per_hour":"18.50"}'
   ```
   Use `/cars/my-cars` to verify, `/cars/<id>` to fetch, or `/cars/<id>` with `PUT`/`DELETE` to manage.

5. **Public discovery**
   Anyone (no auth) can browse:
   ```bash
   curl "http://localhost:5005/cars/query-cars?make=tesla&max_price=20&page=1&per_page=5"
   ```
   The response returns `cars` plus `pagination` metadata a UI can paginate on.

6. **Driver rents and returns**
   ```bash
   # Login as driver and capture cookie
   curl -X POST http://localhost:5005/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"driver@example.com","password":"Pass123!"}' \
     -c driver-cookie.txt

   # Rent a specific car
   curl -X POST http://localhost:5005/rentals/rent/1 -b driver-cookie.txt

   # Return the active rental (fee is auto-calculated)
   curl -X POST http://localhost:5005/rentals/return -b driver-cookie.txt
   ```
   Drivers can inspect their history at `/rentals/user/history` or use `/rentals/user/query` with rich filters such as `status=completed&rental_date_start=2024-01-01`.

7. **Merchant analytics**
   Merchants access `/rentals/merchant/history` or `/rentals/merchant/query?status=completed&min_fee=30` to understand fleet utilization and revenue per booking.
