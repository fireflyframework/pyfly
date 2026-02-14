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

## What is PyFly?

PyFly is the **official native Python implementation** of the [Firefly Framework](https://github.com/fireflyframework) — a comprehensive enterprise framework originally built on **Spring Boot** for the Java ecosystem.

The Firefly Framework provides a battle-tested set of enterprise patterns: dependency injection, CQRS, event-driven architecture, hexagonal design, distributed transactions, and more. With **PyFly**, all of these patterns come to Python 3.12+ — reimagined from the ground up for `async/await`, type hints, protocols, and the full power of modern Python.

> **Why PyFly?** The Firefly Framework's Java implementation (`fireflyframework-*`) consists of 40+ Spring Boot modules covering everything from kernel abstractions to workflow engines, event sourcing, and enterprise content management. PyFly brings this same cohesive programming model to Python — not as a port or wrapper, but as a **native implementation** that embraces Python's strengths while preserving the architectural patterns that make the Firefly Framework production-ready.

### Who is PyFly for?

- **Firefly Framework users** who need Python services that share the same architecture and patterns as their Java services
- **Teams migrating from Java/Spring Boot** who want familiar concepts expressed natively in Python
- **Python developers** who want enterprise-grade patterns without reinventing the wheel
- **Architects** building polyglot microservice platforms who need consistency across Java and Python services

If you're coming from Spring Boot or the Firefly Framework for Java, check out our [Spring Boot Comparison Guide](docs/spring-comparison.md) for a detailed mapping of concepts.

---

## Philosophy

PyFly is guided by the same core beliefs as the Firefly Framework:

### Convention Over Configuration

A new project works out of the box with zero configuration. The framework ships with production-ready defaults for every module — logging levels, connection pool sizes, retry policies, security headers, and more. When you need to customize, override only what matters.

```yaml
# This is ALL you need for a working web service:
pyfly:
  web:
    port: 8080
```

### Framework-Agnostic Domain Logic

Your business code should never depend on infrastructure libraries. PyFly enforces this through **hexagonal architecture (ports and adapters)** — the same pattern used across all Firefly Framework modules:

- **Ports** are Python `Protocol` classes defining contracts
- **Adapters** are concrete implementations (SQLAlchemy, Redis, Kafka, etc.)
- Your services depend on ports, never on adapters

This means you can swap your database, message broker, or cache backend without touching a single line of business logic.

### Async-First, Type-Safe

Every PyFly API is designed for `asyncio` from the ground up — no sync-to-async bridges, no thread pool workarounds. Every public API has complete type annotations, validated by mypy in strict mode.

### Production-Ready by Default

Every PyFly application ships with structured logging, correlation IDs, health check endpoints, Prometheus metrics, OWASP security headers, graceful startup/shutdown, and more — built in from day one.

---

## Core Concepts

### Hexagonal Architecture

Every module that interacts with external systems follows the ports and adapters pattern. Your services depend on `Protocol` contracts; concrete implementations are resolved by the DI container at startup.

```
┌──────────────────────────────────────────────┐
│              Your Application                │
│                                              │
│   @service                 @repository       │
│   class OrderService:      class OrderRepo:  │
│       repo: RepositoryPort     ...           │
│       broker: MessageBrokerPort              │
│       cache: CacheAdapter                    │
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

### Dependency Injection

PyFly's DI container supports **constructor injection** and **field injection** based on type hints — no XML, no reflection, just Python decorators and type annotations:

```python
from pyfly.container import Autowired, service

@service
class OrderService:
    metrics: MetricsCollector = Autowired(required=False)  # field injection

    def __init__(self, repo: OrderRepository, events: EventPublisher) -> None:
        self._repo = repo      # constructor injection (preferred)
        self._events = events
```

The container inspects `__init__` parameters and `Autowired()` fields, resolves dependencies recursively, and manages bean lifecycles (singleton, transient, request-scoped). It also supports `Optional[T]` (resolves to `None` when missing), `list[T]` (collects all implementations), `Qualifier` for named beans, and automatic circular dependency detection.

### Auto-Configuration

PyFly detects installed libraries at startup and wires the appropriate adapters automatically. Redis installed? Cache uses `RedisCacheAdapter`. No broker library? Messaging uses `InMemoryMessageBroker`. You can always override with explicit configuration.

---

## Installation

> **Note:** PyFly is distributed exclusively via GitHub. It is **not** published to PyPI.

### Quick Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/fireflyframework/pyfly.git
cd pyfly

# Run the installer (creates a venv, installs PyFly, adds to PATH)
bash install.sh
```

### Manual Install

```bash
# Clone the repository
git clone https://github.com/fireflyframework/pyfly.git
cd pyfly

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install with all modules
pip install -e ".[full]"

# Or install with specific extras only
pip install -e ".[web,data,security,cli]"
```

### Verify Installation

```bash
pyfly --version
pyfly doctor
pyfly info
```

### Create Your First Project

```bash
pyfly new my-service
cd my-service
pyfly run --reload

# Visit the API docs
open http://localhost:8080/docs
```

See the [Installation Guide](docs/installation.md) for detailed options, Docker examples, and CI/CD setup.

---

## Modules

PyFly currently implements **22 modules** organized into four layers:

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
| **Data** | Repository pattern, specifications, pagination | `fireflyframework-r2dbc` |
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

Browse all guides in the [Documentation Table of Contents](docs/README.md).

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

**Current:** v0.1.0-alpha (2026-02-14) — 22 modules across 4 layers, interactive installer, full CLI tooling.

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
