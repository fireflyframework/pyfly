<p align="center">
  <img src="assets/pyfly-logo.png" alt="PyFly Logo" width="600" />
</p>

<p align="center">
  <strong>The Official Python Implementation of the Firefly Framework</strong>
</p>

<p align="center">
  <a href="https://github.com/fireflyframework"><img src="https://img.shields.io/badge/Firefly_Framework-official-ff6600?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMiAyQzYuNDggMiAyIDYuNDggMiAxMnM0LjQ4IDEwIDEwIDEwIDEwLTQuNDggMTAtMTBTMTcuNTIgMiAxMiAyeiIvPjwvc3ZnPg==" alt="Firefly Framework"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.12%2B-blue?logo=python&logoColor=white" alt="Python 3.12+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-green" alt="License: Apache 2.0"></a>
  <a href="#"><img src="https://img.shields.io/badge/version-0.1.0--alpha-yellow" alt="Version: 0.1.0-alpha"></a>
  <a href="#"><img src="https://img.shields.io/badge/type--checked-mypy%20strict-blue?logo=python&logoColor=white" alt="Type Checked: mypy strict"></a>
  <a href="#"><img src="https://img.shields.io/badge/code%20style-ruff-purple?logo=ruff&logoColor=white" alt="Code Style: Ruff"></a>
  <a href="#"><img src="https://img.shields.io/badge/async-first-brightgreen" alt="Async First"></a>
</p>

<p align="center">
  <em>Build production-grade Python applications with the patterns you trust — dependency injection, CQRS, event-driven architecture, and more — powered by the <a href="https://github.com/fireflyframework">Firefly Framework</a>.</em>
</p>

---

## The Problem

You've been here before. A new Python microservice needs to ship. Before writing a single line of business logic, you spend the first two weeks making choices:

- Which web framework? (FastAPI, Flask, Starlette, Django...)
- Which ORM? (SQLAlchemy, Tortoise, Django ORM...)
- Which message broker? (aiokafka, aio-pika, kombu...)
- How do you wire dependencies? (dependency-injector, python-inject, manual...)
- How do you structure the project? (Everyone invents their own layout)

You assemble a bespoke stack, glue it together, and move on. Six months later, another team builds a second service — and makes entirely different choices. Now you have two codebases with different conventions, different testing strategies, different deployment patterns, and no shared understanding of how things work.

**Python gives you infinite choice. What it doesn't give you is cohesion.**

---

## What is PyFly?

PyFly makes these decisions for you.

It is a **cohesive, full-stack framework** for building production-grade Python applications — microservices, monoliths, and libraries — where every module is designed to work together seamlessly. Dependency injection, HTTP routing, database access, messaging, caching, security, observability, and more — all integrated, all consistent, all with production-ready defaults from day one.

```python
from pyfly.container import service
from pyfly.web import rest_controller, get_mapping

@service
class OrderService:
    def __init__(self, repo: OrderRepository, events: EventPublisher) -> None:
        self._repo = repo
        self._events = events

    async def place_order(self, order: Order) -> Order:
        saved = await self._repo.save(order)
        await self._events.publish(OrderPlaced(order_id=saved.id))
        return saved

@rest_controller("/orders")
class OrderController:
    def __init__(self, service: OrderService) -> None:
        self._service = service

    @post_mapping
    async def create(self, order: Valid[Body[Order]]) -> Order:
        return await self._service.place_order(order)
```

No boilerplate. No manual wiring. The DI container resolves `OrderRepository` and `EventPublisher` from type hints, validates the request body, and publishes domain events — all out of the box.

PyFly is the **official Python implementation** of the [Firefly Framework](https://github.com/fireflyframework), a battle-tested enterprise platform originally built on Spring Boot for Java (40+ modules in production). PyFly brings the same cohesive programming model to Python 3.12+ — not as a port, but as a **native implementation** reimagined for `async/await`, type hints, protocols, and the full power of modern Python.

### Who is PyFly for?

- **Python developers** who want enterprise-grade patterns without reinventing the wheel for every project
- **Teams** tired of assembling bespoke stacks and want every service to follow the same conventions
- **Architects** building polyglot platforms who need consistency across Java and Python services
- **Anyone migrating from Spring Boot** who wants familiar concepts expressed natively in Python

Coming from Spring Boot? See the [Spring Boot Comparison Guide](docs/spring-comparison.md) for a side-by-side concept mapping.

---

## Philosophy

Four principles shape every design decision in PyFly. Together, they answer a single question: *how do you build applications that are easy to start, easy to change, and ready for production from the first commit?*

### Convention Over Configuration

Starting a new project should take seconds, not days. PyFly ships with production-ready defaults for every module — logging formats, connection pool sizes, retry policies, security headers, health endpoints — so a new service works immediately with minimal configuration:

```yaml
# A complete, production-ready web service:
pyfly:
  web:
    port: 8080
```

When you need to customize, you override only what matters. Everything else stays sensible.

### Your Code, Not Ours

Your business logic should never import `sqlalchemy`, `redis`, `aiokafka`, or any other infrastructure library. PyFly enforces this through **hexagonal architecture** — the same ports-and-adapters pattern used across all Firefly Framework modules:

- **Ports** are Python `Protocol` classes that define contracts
- **Adapters** are concrete implementations that fulfill those contracts
- Your services depend on ports. The DI container wires the adapters at startup.

The result: you can swap your database from PostgreSQL to MongoDB, your broker from Kafka to RabbitMQ, or your cache from Redis to in-memory — without touching a single line of business logic.

### Async-Native, Type-Safe

Every PyFly API is designed for `asyncio` from the ground up — no sync-to-async bridges, no thread pool workarounds. Every public surface has complete type annotations validated by mypy in strict mode. If it compiles, it's consistent.

### Production-Ready from Day One

The first time you run `pyfly run`, your application already has structured logging with correlation IDs, health check endpoints, Prometheus metrics, OWASP security headers, and graceful shutdown. These aren't features you opt into — they're the baseline.

---

## How It Works

### Dependency Injection

PyFly's DI container resolves dependencies from type hints — no XML, no reflection, just decorators and annotations:

```python
from pyfly.container import Autowired, service

@service
class OrderService:
    metrics: MetricsCollector = Autowired(required=False)  # field injection

    def __init__(self, repo: OrderRepository, events: EventPublisher) -> None:
        self._repo = repo      # constructor injection (preferred)
        self._events = events
```

The container inspects `__init__` parameters and `Autowired()` fields, resolves dependencies recursively, and manages bean lifecycles (singleton, transient, request-scoped). It supports `Optional[T]` (resolves to `None` when missing), `list[T]` (collects all implementations), `Qualifier` for named beans, and automatic circular dependency detection.

### Hexagonal Architecture

Every module that interacts with external systems follows the ports-and-adapters pattern. Your services depend on `Protocol` contracts; the DI container binds concrete implementations at startup:

```
┌──────────────────────────────────────────────┐
│              Your Application                │
│                                              │
│   @service                 @repository       │
│   class OrderService:      class OrderRepo:  │
│       repo: RepositoryPort     ...           │
│       broker: MessageBrokerPort              │
│       cache: CachePort                       │
│                                              │
│           Depends on PORTS (Protocols)       │
│                    │                         │
├────────────────────┼─────────────────────────┤
│                    │                         │
│    ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│    │SQLAlchemy│ │  Kafka   │ │  Redis   │    │
│    │ Adapter  │ │ Adapter  │ │ Adapter  │    │
│    └──────────┘ └──────────┘ └──────────┘    │
│                                              │
│           ADAPTERS (Implementations)         │
└──────────────────────────────────────────────┘
```

### Auto-Configuration

PyFly detects installed libraries at startup and wires the right adapters automatically. `sqlalchemy` installed? Data uses `Repository`. `redis` installed? Cache uses `RedisCacheAdapter`. No broker library? Messaging falls back to `InMemoryMessageBroker`. You can always override with explicit configuration — but you rarely need to.

---

## Installation

> **Note:** PyFly is distributed exclusively via GitHub. It is **not** published to PyPI.

### One-Line Install (Recommended)

```bash
# Via get.pyfly.io
curl -fsSL https://get.pyfly.io/ | bash

# Or directly from GitHub
curl -fsSL https://raw.githubusercontent.com/fireflyframework/pyfly/main/install.sh | bash
```

The installer clones the repo, creates a virtual environment, installs PyFly with all extras, and adds `pyfly` to your PATH. You can customize with environment variables:

```bash
# Install to a custom directory
PYFLY_HOME=/opt/pyfly curl -fsSL https://get.pyfly.io/ | bash

# Install with specific extras only
PYFLY_EXTRAS=web,data-relational,security curl -fsSL https://get.pyfly.io/ | bash
```

### Local Install (from source)

```bash
# Clone the repository
git clone https://github.com/fireflyframework/pyfly.git
cd pyfly

# Run the interactive installer
bash install.sh

# Or install manually with pip
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[full]"
```

### Verify Installation

```bash
pyfly --version
pyfly doctor
pyfly info
```

### Create Your First Project

```bash
# Quick start — create a REST API with all the batteries
pyfly new my-service --archetype web-api
cd my-service
pyfly run --reload

# Visit http://localhost:8080/health
```

See the [Installation Guide](docs/installation.md) for detailed options, Docker examples, and CI/CD setup.

---

## CLI & Project Scaffolding

The `pyfly` CLI generates production-ready project structures with DI stereotypes, Docker support, and layered architecture out of the box.

### Archetypes

| Command | What you get |
|---------|-------------|
| `pyfly new my-app` | Minimal microservice (`core` archetype) |
| `pyfly new my-api --archetype web-api` | REST API with controllers, services, repositories |
| `pyfly new my-svc --archetype hexagonal` | Hexagonal architecture with ports & adapters |
| `pyfly new my-lib --archetype library` | Reusable library with `py.typed` marker |

### Feature Selection

Choose which PyFly extras to include with `--features`:

```bash
# REST API with database and caching
pyfly new order-service --archetype web-api --features web,data-relational,cache
```

Available features: `web`, `data-relational`, `data-document`, `eda`, `cache`, `client`, `security`, `scheduling`, `observability`, `cqrs`

### Interactive Mode

Run `pyfly new` without arguments for a guided experience:

```
$ pyfly new

  ╭─ PyFly Project Generator ─╮
  ╰────────────────────────────╯
  Project name: order-service
  Package name [order_service]:
  Archetype:
    1) core         Minimal microservice
    2) web-api      Full REST API with layered architecture
    3) hexagonal    Hexagonal architecture (ports & adapters)
    4) library      Reusable library package
  Select archetype [1]: 2
  Features (comma-separated, enter for defaults) [web]: web,data-relational
```

### Generated Web API Structure

```
order-service/
├── Dockerfile              # Multi-stage production build
├── README.md               # Project docs with quick start
├── pyfly.yaml              # Framework configuration
├── pyproject.toml           # Dependencies based on selected features
├── .env.example
├── src/order_service/
│   ├── app.py              # @pyfly_application entry point
│   ├── controllers/
│   │   ├── health_controller.py   # @rest_controller — /health
│   │   └── item_controller.py     # @rest_controller — CRUD /items
│   ├── services/
│   │   └── item_service.py        # @service — business logic
│   ├── models/
│   │   └── item.py                # Pydantic DTOs
│   └── repositories/
│       └── item_repository.py     # @repository — data access
└── tests/
    └── test_item_controller.py
```

### Other CLI Commands

| Command | Description |
|---------|-------------|
| `pyfly run --reload` | Start the application server with auto-reload |
| `pyfly info` | Show installed framework version and extras |
| `pyfly doctor` | Diagnose your development environment |
| `pyfly db init` | Initialize Alembic migration environment |
| `pyfly db migrate -m "msg"` | Auto-generate a database migration |
| `pyfly db upgrade` | Apply pending migrations |

See the full [CLI Reference](docs/cli.md) for details.

---

## Modules

PyFly currently implements **23 modules** organized into four layers:

### Foundation Layer

| Module | Description | Firefly Java Equivalent |
|--------|-------------|------------------------|
| **Core** | Application bootstrap, lifecycle, banner, configuration | `fireflyframework-core` |
| **Kernel** | Exception hierarchy, structured error types | `fireflyframework-kernel` |
| **Container** | Dependency injection, stereotypes, bean factories | Spring DI (built-in) |
| **Context** | ApplicationContext, events, lifecycle hooks, conditions | Spring ApplicationContext |
| **Config** | Auto-configuration engine with provider detection | Spring Auto-Configuration |
| **Logging** | Structured logging port and adapters | `fireflyframework-observability` |

### Application Layer

| Module | Description | Firefly Java Equivalent |
|--------|-------------|------------------------|
| **Web** | HTTP routing, controllers, middleware, OpenAPI | `fireflyframework-web` |
| **Data Relational** | Repository pattern, specifications, pagination (SQLAlchemy) | `fireflyframework-r2dbc` |
| **Data Document** | Document database support (MongoDB via Beanie ODM) | `fireflyframework-mongodb` |
| **CQRS** | Command/Query segregation with mediator | `fireflyframework-cqrs` |
| **Validation** | Input validation with Pydantic | `fireflyframework-validators` |

### Infrastructure Layer

| Module | Description | Firefly Java Equivalent |
|--------|-------------|------------------------|
| **Security** | JWT, password encoding, authorization | Part of `fireflyframework-application` |
| **Messaging** | Kafka, RabbitMQ, in-memory broker | `fireflyframework-eda` |
| **EDA** | Event-driven architecture, event bus | `fireflyframework-eda` |
| **Cache** | Caching decorators, Redis adapter | `fireflyframework-cache` |
| **Client** | HTTP client, circuit breaker, retry | `fireflyframework-client` |
| **Scheduling** | Cron jobs, fixed-rate tasks | Spring Scheduling |
| **Resilience** | Rate limiter, bulkhead, timeout, fallback | Resilience4j (in `fireflyframework-client`) |

### Cross-Cutting Layer

| Module | Description | Firefly Java Equivalent |
|--------|-------------|------------------------|
| **AOP** | Aspect-oriented programming | Spring AOP |
| **Observability** | Prometheus metrics, OpenTelemetry tracing | `fireflyframework-observability` |
| **Actuator** | Health checks, monitoring endpoints | `fireflyframework-core` (actuator) |
| **Testing** | Test fixtures and assertions | Spring Test |
| **CLI** | Command-line tools | `fireflyframework-cli` |

---

## Documentation

Full documentation lives in the [`docs/`](docs/README.md) directory:

- [Getting Started Tutorial](docs/getting-started.md) — Build your first PyFly application step by step
- [Installation](docs/installation.md) — Install and configure PyFly with the right extras
- [Architecture Overview](docs/architecture.md) — Understand the framework's design and patterns
- [CLI Reference](docs/cli.md) — Command-line tools (new, run, db, info, doctor)
- [Spring Boot Comparison](docs/spring-comparison.md) — Side-by-side concept mapping for Java developers

### Module Guides

Browse all guides in the [Guides Index](docs/guides/README.md):

- [Web Layer](docs/guides/web.md) — REST controllers, routing, parameter binding, OpenAPI
- [Data Relational (SQL)](docs/guides/data-relational.md) — Repositories, derived queries, pagination, transactions
- [Data Document (MongoDB)](docs/guides/data-document.md) — Document database support via Beanie ODM
- [Validation](docs/guides/validation.md) — `Valid[T]` annotation, structured 422 errors
- [WebFilters](docs/guides/web-filters.md) — Request/response filter chain
- [Actuator](docs/guides/actuator.md) — Health checks, extensible endpoints
- [Custom Actuator Endpoints](docs/guides/custom-actuator-endpoints.md) — Build your own actuator endpoints

Browse the full list in the [Documentation Table of Contents](docs/README.md).

---

## Roadmap

See **[ROADMAP.md](ROADMAP.md)** for the full roadmap toward feature parity with the Firefly Framework Java ecosystem (40+ modules).

| Phase | Focus | Key Modules |
|-------|-------|-------------|
| **Phase 1** | Core Distributed Patterns | Event Sourcing, Saga/TCC, Workflow, DDD |
| **Phase 2** | Business Logic | Rule Engine, Plugins, Data Processing |
| **Phase 3** | Enterprise Integrations | Notifications, IDP, ECM, Webhooks |
| **Phase 4** | Administrative | Backoffice, Config Server, Utils |

---

## Changelog

See **[CHANGELOG.md](CHANGELOG.md)** for detailed release notes.

**Current:** v0.1.0-alpha.3 (2026-02-15) — MongoDB support via Beanie ODM, WebFilter chain, `Valid[T]` validation, extensible actuator, config-driven web adapter.

---

## Firefly Framework Ecosystem

PyFly is part of the [Firefly Framework](https://github.com/fireflyframework) ecosystem:

| Platform | Repository | Status |
|----------|-----------|--------|
| **Java / Spring Boot** | [`fireflyframework-*`](https://github.com/fireflyframework) (40+ modules) | Production |
| **Python** | [`pyfly`](https://github.com/fireflyframework/pyfly) | Alpha |
| **Frontend (Angular)** | [`flyfront`](https://github.com/fireflyframework/flyfront) | Active Development |
| **GenAI** | [`fireflyframework-genai`](https://github.com/fireflyframework/fireflyframework-genai) | Active Development |
| **CLI (Go)** | [`fireflyframework-cli`](https://github.com/fireflyframework/fireflyframework-cli) | Active Development |

---

## Requirements

| Requirement | Version |
|-------------|---------|
| Python | >= 3.12 |
| pip | Latest recommended |
| Git | For cloning the repository |
| OS | macOS, Linux (Windows support planned) |

---

## License

Apache License 2.0 — [Firefly Software Solutions Inc.](https://github.com/fireflyframework)
