# Event & Ticket Management System Backend

Asynchronous backend package for event scheduling and concurrent ticket sales. Built with Python using Clean Architecture principles, Repository pattern, and Unit of Work.

The system features advanced asynchronous task queuing, strict data validation pipelines, infrastructure monitoring dashboards, and security isolation designed to handle high-load traffic during peak ticket sales windows.

## Technical Highlights

* **Clean Architecture and Repository Pattern:** Business logic is decoupled from the HTTP layer (FastAPI) and Database layer (SQLAlchemy), communicating via abstract interfaces and isolated within standalone domains.
* **Distributed Idempotency Layer:** Real-time protection for financial and critical endpoints (`/pay`, `/book`) using atomic distributed locking and response-caching via a custom API decorator backed by Redis.
* **Structured Race Condition Protection:** Combined approach utilizing atomic database mutations (`PostgreSQL RETURNING` clauses) for transaction safety and high-performance concurrency limits via short-lived Redis/KeyDB locks.
* **Encapsulated Domain Contexts:** Strict domain partitioning into contexts (user, event, ticket, views). Modules are grouped as namespaces to prevent variable shadowing in the application code.
* **Asynchronous Background Processing:** Native integration with TaskIQ for non-blocking task orchestration and scheduled lock-releases for expired, unpaid ticket reservations.
* **High-Performance Telemetry System:** Real-time event view counter engine powered by memory-efficient Redis HyperLogLog (`PFADD`, `PFCOUNT`) structures, ensuring fast deduplication of unique visitor interactions.
* **Production Monitoring Stack:** Native Prometheus metrics engine paired with Grafana dashboards to track latency percentiles, error rates, and request throughput in real time.
* **Comprehensive Integration Testing:** Automated testing suite leveraging TaskIQ in-memory scheduling running in `await_inplace` mode to catch side-effects within a single structured `asyncio.TaskGroup` lifecycle.

## Tech Stack

* **Package Manager:** uv
* **Framework:** FastAPI
* **Database ORM:** SQLAlchemy 2.0 and Alembic (PostgreSQL)
* **Validation:** Pydantic v2
* **Task Queue:** TaskIQ and TaskIQ-Redis
* **Distributed Cache:** KeyDB (High-performance Redis multi-threaded alternative)
* **Telemetry Engine:** Prometheus Client & Grafana UI
* **Testing:** Pytest, Pytest-asyncio, and Httpx
* **Containerization:** Docker and Docker Compose

## Features

### User and Access Management
* Registration and authentication via cryptographically hashed passwords and JWT tokens.
* Weight-based role hierarchy including user, on_verification, verified_user, moderator, and admin.
* Automated ticket migration transferring anonymous ticket holdings to a user profile upon official registration.
* System Management CLI: Administrative commands executed within runtime containers to instantly seed privileged users or mock dataset.

### Event Orchestration
* Multi-level event categorization with parent path validation.
* Event drafts with complex cross-field validation rules restricting physical addresses to offline venues.
* Moderation workflows for newly submitted events and user verification applications.
* Scalable telemetry engine tracking dynamic view milestones across unique timeframes.

### High-Concurrency Ticket Sales
* Dynamic allocation of ticket types to specified event instances.
* Dual-mode booking engine for authenticated users and guest checkouts protected against double-booking via custom idempotency keys.
* Automated task hooks releasing expired, unpaid ticket holdings back into available inventory after 15 minutes.

## File Structure

```text
.
├── docker-compose.yml          # Core production multi-container setup (API, Workers, DB)
├── docker-compose.demo.yml     # Infrastructure container orchestration with exposed monitoring
├── docker-compose.prod.yml     # Hardened production extensions, reverse proxy volumes, and security
├── docker-compose.test.yml     # Isolated test environment orchestration
├── .env.example                # Blueprint for required environment variables
├── .gitignore                  # Root Git exclusion rules
├── LICENSE                     # Project software license agreement
├── nginx.conf.template         # Dynamic template for Nginx reverse proxy configurations
└── backend/                    # Core backend service directory
    ├── Dockerfile              # Multi-stage container build rules (test, lint, backend) using uv
    ├── pyproject.toml          # Main project metadata and tool configurations
    ├── uv.lock                 # Strict dependency lockfile
    ├── prometheus.yml          # Prometheus config file
    ├── alembic.ini             # Database migration configuration metadata
    ├── alembic/                # Database migration scripts and environment
    ├── tests/                  # Integration test cases, fixtures, and conftest
    └── src/                    # Source root
        ├── app/                # Application Assembly & Command Center
        │   ├── main.py         # Main FastAPI application entrypoint and exception mapping
        │   ├── routes.py       # Global root router mounting point (/api/v1)
        │   ├── metrics.py      # Prometheus instrumentation and scrapers bootstrapper
        │   ├── exceptions.py   # Pure domain business exceptions hierarchy
        │   └── uow.py          # Strict declaration of application-specific Unit of Work
        ├── cli/                # Terminal-executable administration modules
        ├── domain/             # Business Logic & Contracts (Pure Python)
        │   └── services/       # Base generic service implementation contracts
        ├── core/               # App configuration, security and database infrastructure
        │   ├── settings.py     # Pydantic Settings global env state parsing
        │   ├── database.py     # Lazy thread-safe SQLAlchemy AsyncEngine Factory
        │   ├── annotations.py  # Shared generic TypeVars for strict type checking
        │   ├── security/       # JWT token utilities and cryptographic password handlers
        │   └── infra/          # Abstract Technical Framework Wrappers
        │       ├── cache/      # Lazy CacheManagerFactory (Redis / InMemory implementations)
        │       ├── tasks/      # Lazy TaskManagerFactory, configurations, and TaskIQ Broker
        │       ├── mail/       # Flat asynchronous email dispatcher domain (Jinja2, FastMail)
        │       └── transport/  # HTTP Transport components and Idempotency Decorator
        └── modules/            # Isolated Domain Partitions (Business Features)
            ├── admin/          # Administration and system control endpoints
            ├── event/          # Venues, category mappings, and event routes
            ├── ticket/         # Inventory allocation, checkout, and cleanup tasks
            └── user/           # User profiles, weight roles, and validation tasks
```
## Infrastructure Design

The application separates concerns into distinct execution contexts via optimized container configurations:

* **Core Architecture Stack (`docker-compose.yml`):** The primary local and testing configuration containing the core database, KeyDB cache, TaskIQ workers, and the full telemetry suite (**Prometheus** and **Grafana**) with exposed host ports and dynamic volumes for active development (`--reload`).
* **Demonstration Setup (`docker-compose.demo.yml`):** A streamlined web-only demonstration context that focuses strictly on the application lifecycle, deploying the isolated services behind an **Nginx** reverse proxy using separate network zones (`frontend_network` and `backend_network`) while stripping out the telemetry layer.
* **Hardened Production Overlay (`docker-compose.prod.yml`):** A production extension layer designed to be stacked directly on top of the core configuration. It safely drops dynamic telemetry port exposures from the host boundaries (`ports: !reset []`) to secure the private network perimeter and maps data onto persistent production volumes (`prometheus_data`, `grafana_data`).
* **Optimized Multi-Stage Build (`Dockerfile`):** Implements specialized build target stages (`test`, `lint`, `backend`) powered by `uv` for minimal image foot-printing. The target production stage selectively copies only application source files using build filters, completely excluding testing files to ensure an optimal and secure production environment.
* **Telemetry Engine:** Integrated Prometheus scraper pulling HTTP execution duration histograms, process memory footprints, and raw connection states. Metrics endpoints are protected from external polling by static Bearer Token gates mounted natively via Docker Secrets.
* **Healthcheck Dependency Chains:** All containers utilize 24/7 internal healthcheck probes (`urllib.request`, `nc`, `pg_isready`). Orchestration constraints enforce strict initialization sequencing so dependent components only load after upstream databases, caches, and proxies return definitive health signals.

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

#### Run Local Core & Telemetry Stack (Development)
```bash
docker compose -f docker-compose.yml up -d --build
```
* The interactive API documentation will be available at http://localhost:8000/docs
* The local Prometheus metrics scraping instance will be available at http://localhost:9090
* The Grafana telemetry dashboard will be available at http://localhost:3000

#### Run Lightweight Demo Stack (With Nginx Proxy)
```bash
docker compose -f docker-compose.demo.yml up -d --build
```

#### Run Hardened Production Environment
To deploy the secure, production-ready infrastructure with private telemetry storage networks and strict boundary firewalls, stack the core configuration together with the production overlay:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## System Administration Command Line

Privileged user configuration and dataset generation bypasses raw database connection management through an abstracted CLI module inside the runtime engine.

### User Management Commands
To securely create administrative accounts with automatic cryptographic password hashing, execute the Python module directly inside the active service container:

```bash
# Create an Administrator account
docker exec -it api python -m src.cli.create_user admin@ticket.com your_password admin

# Create a Moderator account
docker exec -it api python -m src.cli.create_user moderator@ticket.com your_password moderator
```

#### Expected Terminal Output:
```text
Creating user admin@ticket.com with role admin...
User admin@ticket.com successfully created with role admin
```

### Database Seeding Commands
To populate the database tables with structural mock dataset (including event categories, sample venues, and ticket pricing tiers) for rapid staging or testing purposes, run the system seed script:

```bash
# Seed full initial structural data
docker exec -it api python -m src.cli.seed_system_data
```

## Testing Suite

The application implements a zero-network dependent testing suite using isolated database transactions, fully synchronized `InMemoryCacheManager` states, and TaskIQ in-memory scheduling.

### Running Containerized Tests
The testing infrastructure is completely separated into an isolated project context to prevent environment state mutation or pipeline data pollution.

To execute the full test pack with code coverage reporting within a self-terminating container loop:
```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

## Implementation Notes

Core modules demonstrating engineering depth for review:

1. `src/core/infra/transport/http/idempotency.py`: Reusable API decorator utilizing atomic lock check/set routines and automated model serialization to guarantee transaction safety across high-load request loops.
2. `src/modules/ticket/repositories.py`: Contains atomic state transformations using SQL expressions combined with returning properties to prevent race conditions during high-volume purchasing bursts.
3. `src/app/uow.py` & `src/core/infra/database/uow.py`: Demonstrates decoupling patterns, enabling developers to fully swap out data infrastructures or mock network layers without breaking core features.
4. `src/core/infra/cache/managers/in_memory.py`: Custom isolated test-double caching module replicating standard production Redis operations, context locks, and HyperLogLog pipelines natively in volatile memory.
