# Event & Ticket Management System Backend

Asynchronous backend package for event scheduling and concurrent ticket sales. Built with Python using Clean Architecture principles, Repository pattern, and Unit of Work.

The system features advanced asynchronous task queuing, strict data validation pipelines, infrastructure monitoring dashboards, and security isolation designed to handle high-load traffic during peak ticket sales windows.

## Technical Highlights

* Clean Architecture and Repository Pattern: Business logic is decoupled from the HTTP layer (FastAPI) and Database layer (SQLAlchemy), communicating via abstract interfaces.
* Atomic State Mutations: Ticket reservation and payment use atomic UPDATE statements combined with PostgreSQL RETURNING clauses to prevent race conditions without excessive locks.
* Encapsulated Domain Contexts: Strict domain partitioning into contexts (user, event, ticket). Modules are grouped as namespaces to prevent variable shadowing in the application code.
* Asynchronous Background Processing: Native integration with Taskiq for non-blocking task orchestration and scheduled lock-releases for unpaid ticket reservations.
* Production Monitoring Stack: Native Prometheus metrics engine paired with Grafana dashboards to track latency percentiles, error rates, and request throughput in real time.
* Network and API Security: Endpoint protection via dynamic token mapping and Docker Secrets isolation, combined with strategic 404 Not Found masking to prevent resource harvesting.
* Comprehensive Integration Testing: Automated testing suite leveraging Taskiq in-memory scheduling running in await_inplace mode to catch side-effects within a single transaction.

## Tech Stack

* Package Manager: uv
* Framework: FastAPI
* Database ORM: SQLAlchemy 2.0 and Alembic
* Validation: Pydantic v2
* Task Queue: Taskiq and Taskiq-Redis
* Distributed Cache: KeyDB (High-performance Redis multi-threaded alternative)
* Telemetry Engine: Prometheus Client & Grafana UI
* Testing: Pytest, Pytest-asyncio and Httpx
* Containerization: Docker and Docker Compose
* Environment: Python 3.12+, PostgreSQL, Redis

## Features

### User and Access Management
* Registration and authentication via cryptographically hashed passwords, and JWT tokens.
* Weight-based role hierarchy including user, on_verification, verified_user, moderator, and admin.
* Automated ticket migration transferring anonymous ticket holdings to a user profile upon official registration.
* System Management CLI: Administrative commands executed within runtime containers to instantly seed privileged users.

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
├── docker-compose.yml          # Infrastructure container orchestration (Development)
├── docker-compose.prod.yml     # Production architecture, volumes, and network security
├── docker-compose.test.yml     # Isolated test environment orchestration
├── .env.example                # Blueprint for required local environment variables
└── backend/                    # Core backend service directory
    ├── Dockerfile              # Multi-stage container build rules using uv
    ├── pyproject.toml          # Main project metadata and tool configurations
    ├── uv.lock                 # Strict dependency lockfile
    ├── prometheus.yml          # Prometheus config file
    ├── alembic/                # Database migration scripts and environment
    ├── tests/                  # Integration test cases, fixtures, and conftest
    └── src/                    # Source root
        ├── app.py              # FastAPI application initialization setup
        ├── routes.py           # Global root router mounting point
        ├── metrics.py          # Prometheus instrumentation bootstrapping logic
        ├── common/             # Shareable codebase, base classes and types
        │   ├── orm/            # Declarative base ORM model bindings
        │   ├── tasks/          # Distributed background task dispatchers contract
        │   └── uow/            # Transaction factory layer and SQLAlchemy contracts
        ├── cli/                # CLI commands to execute in terminal
        ├── core/               # App configuration, security and database infrastructure
        │   └── security/       # JWT token utilities and cryptographic handlers
        └── modules/            # Isolated domain partitions
            ├── admin/          # Administration and system control endpoints
            ├── event/          # Venues, category mappings, and event routes
            ├── ticket/         # Inventory allocation, checkout and cleanup tasks
            └── user/           # User profiles, weight roles, and validation tasks
```

## Infrastructure Design

The application separates concerns into three distinct execution contexts via optimized container configurations:

* Development Environment (`docker-compose.yml`): Exposed control interfaces for quick testing, including real-time hot-reloading (`--reload`) and debugging panels.
* Production Environment (`docker-compose.prod.yml`): Hardened runtime configuration utilizing persistent storage volumes for telemetry time-series and database pools. All internal monitoring ports are dropped from host bindings to enforce complete private-network boundaries.
* Telemetry Engine: Integrated Prometheus scraper pulling HTTP execution duration histograms, process memory footprints, and raw connection states. Metrics endpoints are protected from external polling by static Bearer Token gates mounted natively via Docker Secrets.
* Healthcheck Dependency Chains: All containers utilize 24/7 internal healthcheck probes (`urllib.request`, `nc`, `pg_isready`). Orchestration constraints enforce strict initialization sequencing so dependent components only load after upstream databases, caches, and proxies return definitive health signals.

## Installation and Setup

### 1. Clone the repository
```bash
git clone https://github.com
cd ticket-booking-system
```

### 2. Configure Environment Variables
Copy the template file to build your active configuration:
```bash
cp .env.example .env
```
Fill in the secure values inside the newly created `.env` file.

### 3. Run Environments

#### Run Local Development Environment
```bash
docker compose up -d --build
```
The interactive API documentation will be available at http://localhost:8000/docs
The metrics dashboard will be available at http://localhost:3000

#### Run Hardened Production Environment
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## System Administration Command Line

Privileged user configuration bypasses raw database connection management through an abstracted CLI module inside the runtime engine.

To securely create administrative accounts with automatic cryptographic password hashing, execute the Python module directly inside the active service container:

```bash
# Create an Administrator account
docker exec -it fastapi_api python -m src.cli.create_user admin@ticket.com your_password admin

# Create a Moderator account
docker exec -it fastapi_api python -m src.cli.create_user moderator@ticket.com your_password moderator
```

#### Expected Terminal Output:
```text
Creating user admin@ticket.com with role admin...
User admin@ticket.com successfully created with role admin
```

## Testing Suite

The application implements a zero-network dependent testing suite using isolated database transactions and Taskiq in-memory scheduling.

### Running Containerized Tests
The testing infrastructure is completely separated into an isolated project context to prevent environment state mutation or pipeline data pollution.

To execute the test pack with code coverage reporting within a self-terminating container loop:
```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

## Implementation Notes

Core modules demonstrating engineering depth for review:

1. `src/modules/ticket/repositories.py`: Contains atomic state transformations using SQL expressions combined with returning properties to prevent race conditions during high-volume purchasing bursts.
2. `src/common/repositories.py` & `src/core/uow.py`: Demonstrates decoupling patterns, enabling developers to fully swap out data infrastructures or mock network layers without breaking core features.
3. `src/modules/event/schemas.py`: Features multi-field dependent validation schemas, preventing runtime exceptions from parsing raw input variables.
4. `src/metrics.py`: Abstracted dynamic interceptor registry preventing circular module references and enforcing unidirectional dependency hierarchies during boot cycles.
