# Event & Ticket Management System Backend

Asynchronous backend package for event scheduling and concurrent ticket sales. Built with Python using Clean Architecture principles, Repository pattern, and Unit of Work.

The system features advanced asynchronous task queuing, strict data validation pipelines, and security isolation designed to handle high-load traffic during peak ticket sales windows.

## Technical Highlights

* Clean Architecture and Repository Pattern: Business logic is decoupled from the HTTP layer (FastAPI) and Database layer (SQLAlchemy), communicating via abstract interfaces.
* Atomic State Mutations: Ticket reservation and payment use atomic UPDATE statements combined with PostgreSQL RETURNING clauses to prevent race conditions without excessive locks.
* Encapsulated Domain Contexts: Strict domain partitioning into contexts (user, event, ticket). Modules are grouped as namespaces to prevent variable shadowing in the application code.
* Asynchronous Background Processing: Native integration with Taskiq for non-blocking task orchestration and scheduled lock-releases for unpaid ticket reservations.
* Security by Obscurity: Unauthorized mutations of external records dynamically mask resources with 404 Not Found statuses instead of 403 Forbidden to prevent ID harvesting.
* Comprehensive Integration Testing: Automated testing suite leveraging Taskiq in-memory scheduling running in await_inplace mode to catch side-effects within a single transaction.

## Tech Stack

* Package Manager: uv
* Framework: FastAPI
* Database ORM: SQLAlchemy 2.0 and Alembic
* Validation: Pydantic v2
* Task Queue: Taskiq and Taskiq-Redis
* Distributed Cache: KeyDB (High-performance Redis multi-threaded alternative)
* Testing: Pytest, Pytest-asyncio and Httpx
* Containerization: Docker and Docker Compose
* Environment: Python 3.12+, PostgreSQL, Redis

## Features

### User and Access Management
* Registration and authentication via cryptographically hashed passwords and JWT tokens.
* Weight-based role hierarchy including user, on_verification, verified_user, moderator, and admin.
* Automated ticket migration transferring anonymous ticket holdings to a user profile upon official registration.

### Event Orchestration
* Multi-level event categorization with parent path validation.
* Event drafts with complex cross-field validation rules restricting physical addresses to offline venues.
* Moderation workflows for newly submitted events and user verification applications.

### High-Concurrency Ticket Sales
* Dynamic allocation of ticket types to specified event instances.
* Dual-mode booking engine for authenticated users and guest checkouts protected against double-booking.
* Automated task hooks releasing expired, unpaid ticket holdings back into available inventory after 15 minutes.

## File Structure

```text
.
├── docker-compose.yml          # Infrastructure container orchestration
└── backend/                    # Core backend service directory
    ├── Dockerfile              # Multi-stage container build rules using uv
    ├── pyproject.toml          # Main project metadata and tool configurations
    ├── uv.lock                 # Strict dependency lockfile
    ├── alembic/                # Database migration scripts and environment
    ├── tests/                  # Integration test cases, fixtures, and conftest
    └── src/                    # Source root
        ├── app.py              # FastAPI application initialization setup
        ├── routes.py           # Global root router mounting point
        ├── common/             # Shareable codebase, base classes and types
        │   ├── orm/            # Declarative base ORM model bindings
        │   ├── tasks/          # Distributed background task dispatchers contract
        │   └── uow/            # Transaction factory layer and SQLAlchemy contracts
        ├── core/               # App configuration, security and database infrastructure
        │   └── security/       # JWT token utilities and cryptographic handlers
        └── modules/            # Isolated domain partitions
            ├── admin/          # Administration and system control endpoints
            ├── event/          # Venues, category mappings, and event routes
            ├── ticket/         # Inventory allocation, checkout and cleanup tasks
            └── user/           # User profiles, weight roles, and validation tasks
```

## Infrastructure Design

The runtime stack is orchestrated via Docker Compose, leveraging several production-ready container strategies:

* Multi-Stage Builds: Dockerfile separates development dependencies from final production targets, optimizing cache layers and container size via uv.
* KeyDB Engine: Implements KeyDB as a multi-threaded drop-in replacement for Redis, maximizing packet throughput for background processing workers.
* Isolated Database Pools: Spawns two isolated PostgreSQL databases (`db` and `db_test`), entirely insulating production schemas from testing data purges.
* Healthcheck Dependency Chains: Containers utilize strict healthchecks (`pg_isready` and `keydb-cli ping`), ensuring the API, Worker, and Scheduler start only after underlying databases and caches are completely ready.

## Installation and Setup

### 1. Clone the repository
```bash
git clone https://github.com
cd event-ticket-system
```

### 2. Configure Environment Variables
Create a .env file in the root directory using the following template:
```env
DB_PORT=5432
TEST_DB_PORT=5433
REDIS_PORT=6379
BACKEND_PORT=8000

PG_USER=postgres
PG_PASSWORD=postgres
PG_DB=event_db

TEST_PG_USER=postgres
TEST_PG_PASSWORD=postgres
TEST_PG_DB=test_event_db

JWT_SECRET_KEY=your-secure-jwt-secret-key
TEST_JWT_SECRET_KEY=your-secure-test-jwt-secret-key
```

### 3. Run with Docker Compose
```bash
docker compose up -d --build
```

The interactive API documentation will be available at http://127.0.0

## Testing Suite

The application implements a zero-network dependent testing suite using isolated database transactions and Taskiq in-memory scheduling.

### Running Containerized Tests
The container orchestration stack provides an automated `tests` runner service. It waits for the test database to pass healthchecks, executes database migrations, runs all testing files with code coverage tracking, and shuts down safely.

To run the entire test pack inside Docker:
```bash
docker compose run --rm tests
```

## Implementation Notes

Core modules demonstrating engineering depth for review:

1. `src/modules/ticket/repositories.py`: Contains atomic state transformations using SQL expressions combined with returning properties to prevent race conditions during high-volume purchasing bursts.
2. `src/common/repositories.py` & `src/core/uow.py`: Demonstrates decoupling patterns, enabling developers to fully swap out data infrastructures or mock network layers without breaking core features.
3. `src/modules/event/schemas.py`: Features multi-field dependent validation schemas, preventing runtime exceptions from parsing raw input variables.
