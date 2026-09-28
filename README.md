# EVE Healthcare Backend Service

A backend service for diagnostic test bookings and simulated payments, built with FastAPI, PostgreSQL, and SQLAlchemy (async).

## Project Overview
This service provides APIs to manage user authentication, diagnostic centres, test bookings, and a mock payment sequence including an idempotent webhook to update booking states securely.

## Tech Stack
- **Framework**: FastAPI
- **Database**: PostgreSQL (Neon Cloud)
- **ORM & Migrations**: SQLAlchemy (async) + asyncpg, Alembic
- **Testing**: Pytest + HTTPX + aiosqlite (in-memory async testing)
- **Deployment**: Docker & docker-compose

## Database/Schema Design
- **User**: `id`, `email`, `password_hash`, `is_active`, `created_at`
- **DiagnosticCentre**: `id`, `name`, `location`, `created_at`
- **DiagnosticTest**: `id`, `name`, `price`, `centre_id` (FK), `created_at`
- **Booking**: `id`, `user_id` (FK), `test_id` (FK), `centre_id` (FK), `appointment_datetime`, `amount`, `status` (PENDING, CONFIRMED, FAILED, CANCELLED), `created_at`, `updated_at`
- **PaymentEvent**: `id`, `event_id` [UNIQUE], `transaction_id` [UNIQUE], `booking_id` (FK), `status`, `created_at`

## How to Run the Project Locally

### Docker Setup (Recommended)
1. Ensure Docker and Docker Compose are installed.
2. Ensure `.env` is configured properly (the repository holds the safe `.env.example`). 
3. In the root directory, run:
   ```bash
   docker-compose up --build -d backend
   ```
4. The API will be natively available at `http://localhost:8000`. Swagger UI documentation is generated at `http://localhost:8000/docs`.

## API Endpoints and Example Requests

### 1. Authentication
**`POST /auth/signup`**
Creates a new user account.
*Request*:
```json
{
  "email": "test@example.com",
  "password": "password123"
}
```
*Response*:
```json
{
  "id": 1,
  "email": "test@example.com",
  "is_active": true,
  "created_at": "2026-09-28T10:00:00Z"
}
```

**`POST /auth/login`**
Logs the user in and returns a JWT token.
*Request*: (Form Data)
`username=test@example.com` & `password=password123`
*Response*:
```json
{
  "access_token": "eyJhb...",
  "token_type": "bearer"
}
```

### 2. Diagnostic Centres & Tests
**`GET /centres/`**
*Response*:
```json
[
  {
    "name": "Apollo Diagnostics",
    "location": "Downtown Area",
    "id": 1,
    "created_at": "2026-09-28T10:00:00Z"
  }
]
```

**`GET /centres/1/tests/`**
*Response*:
```json
[
  {
    "name": "Complete Blood Count",
    "price": 850.0,
    "centre_id": 1,
    "id": 1,
    "created_at": "2026-09-28T10:00:00Z"
  }
]
```

### 3. Booking System
**`POST /bookings/`** (Requires Auth)
Books an appointment. The server ignores client pricing and securely fetches the test amount natively from the database.
*Request*:
```json
{
  "test_id": 1,
  "centre_id": 1,
  "appointment_datetime": "2026-10-10T10:00:00Z"
}
```
*Response*:
```json
{
  "id": 1,
  "user_id": 1,
  "test_id": 1,
  "centre_id": 1,
  "appointment_datetime": "2026-10-10T10:00:00Z",
  "amount": 850.0,
  "status": "PENDING",
  "created_at": "2026-09-28T10:05:00Z"
}
```

### 4. Payments & Webhooks
**`POST /payments/`** (Requires Auth)
Deterministically simulates a payment transaction.
*Request*:
```json
{
  "booking_id": 1
}
```
*Response*:
```json
{
  "transaction_id": "txn_8a43f9v...",
  "status": "SUCCESS",
  "booking_id": 1
}
```

**`POST /payments/webhook/`**
Updates booking state securely and absolutely idempotently.
*Request*:
```json
{
  "event_id": "evt_webhook_123",
  "transaction_id": "txn_8a43f9v...",
  "booking_id": 1,
  "status": "SUCCESS"
}
```

## Important Assumptions Made
- **Determinism:** For mocking simulated payments without flaky tests, odd `booking_id` amounts resolve to `SUCCESS` and even `booking_id` amounts resolve to `FAILED` for transparent determinism during automated webhook validations.
- **Idempotency Strategy:** Relying on `UNIQUE` constraints on `event_id` and `transaction_id` in the `PaymentEvent` table ensures that concurrent duplicate webhook payload requests hit an `IntegrityError` resulting in an instantaneous safe database rollback, enforcing 100% strict DB-level idempotency without read-before-write race conditions.
- **Testing:** `aiosqlite` is strictly utilized in the test suite (`conftest.py`) to maximize test-run turnaround directly in memory without scaffolding external heavy PostgreSQL testing databases.

## What I Would Improve If I Had More Time
- Implement comprehensive refresh tokens for JWT expiry extensions.
- Enable Redis-backed rate limiting on the `/auth` endpoints to prevent brute-force attacks.
- Provide a robust queuing/worker system (e.g., Celery/RabbitMQ) for sending asynchronous notification emails (Confirmations/Failures) attached to webhook resolutions.
- Implement cursor-based pagination metadata limits for listing tests and bookings.
