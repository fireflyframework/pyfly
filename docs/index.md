# PyFly Framework

**The Enterprise Python Framework**

> *Build production-grade applications with the patterns you trust — dependency injection, CQRS, event-driven architecture, and more — all native to Python.*

---

## Table of Contents

- [What is PyFly?](#what-is-pyfly)
- [Philosophy](#philosophy)
- [Why PyFly?](#why-pyfly)
- [Core Concepts](#core-concepts)
- [Quick Start](#quick-start)
- [Modules](#modules)
- [Documentation](#documentation)

---

## What is PyFly?

PyFly is a comprehensive application framework for Python 3.12+ that brings well-established enterprise patterns to the Python ecosystem. It provides a **cohesive programming model** for building production-grade microservices, monoliths, and libraries — while embracing Python's strengths: `async/await`, type hints, protocols, and simplicity.

Rather than wiring together dozens of independent libraries for each new project, PyFly gives you an opinionated, full-stack foundation where every module is designed to work together seamlessly.

### Who is PyFly for?

- **Teams migrating from Java/Spring** who want familiar concepts expressed natively in Python
- **Python developers** who want enterprise-grade patterns without reinventing the wheel
- **Architects** building microservice platforms who need consistency across services
- **Anyone** tired of choosing from hundreds of libraries and assembling them from scratch

If you're coming from Spring Boot, check out our [Spring Boot Comparison Guide](spring-comparison.md) for a detailed mapping of concepts.

---

## Philosophy

PyFly is guided by four core beliefs:

### Convention Over Configuration

A new project works out of the box with zero configuration. The framework ships with production-ready defaults for every module — logging levels, connection pool sizes, retry policies, security headers, and more. When you need to customize, override only what matters.

```yaml
# This is ALL you need for a working web service:
pyfly:
  web:
    port: 8080
```

### Framework-Agnostic Domain Logic

Your business code should never depend on infrastructure libraries. PyFly enforces this through **hexagonal architecture (ports and adapters)**:

- **Ports** are Python `Protocol` classes defining contracts
- **Adapters** are concrete implementations (SQLAlchemy, Redis, Kafka, etc.)
- Your services depend on ports, never on adapters

This means you can swap your database, message broker, or cache backend without touching a single line of business logic.

### Async-First, Type-Safe

Every PyFly API is designed for `asyncio` from the ground up — no sync-to-async bridges, no thread pool workarounds. Every public API has complete type annotations, validated by mypy in strict mode.

### Production-Ready by Default

Every PyFly application ships with structured logging, correlation IDs, health check endpoints, Prometheus metrics, OWASP security headers, graceful startup/shutdown, and more — built in from day one.

---

## Why PyFly?

### The Problem

Python's ecosystem is vast and vibrant, but building an enterprise application means choosing from hundreds of libraries and wiring them together yourself:

- Which web framework? (FastAPI, Flask, Starlette, Django...)
- Which ORM? (SQLAlchemy, Tortoise, Django ORM...)
- Which message broker client? (aiokafka, aio-pika, kombu...)
- How do you do dependency injection? (dependency-injector, python-inject, manual...)
- How do you handle configuration? (pydantic-settings, python-dotenv, dynaconf...)
- How do you structure the project? (Everyone invents their own layout)

Each project makes different choices, leading to inconsistency across your team's services and constant re-learning.

### The Solution

PyFly makes these decisions for you, providing a **unified, cohesive framework** where all the parts work together:

| Concern | PyFly Module | Underlying Library |
|---------|-------------|-------------------|
| Web framework | `pyfly.web` | Starlette |
| Database access | `pyfly.data` | SQLAlchemy (async) |
| Message broker | `pyfly.messaging` | aiokafka, aio-pika |
| Caching | `pyfly.cache` | Redis (async) |
| HTTP client | `pyfly.client` | httpx |
| Observability | `pyfly.observability` | Prometheus, OpenTelemetry |
| Logging | `pyfly.logging` | structlog |
| Security | `pyfly.security` | PyJWT, bcrypt |
| Validation | `pyfly.validation` | Pydantic |
| CLI tooling | `pyfly.cli` | Click, Rich |

The key difference: **you depend on PyFly's ports (protocols), not on these libraries directly**. If tomorrow a better ORM appears, PyFly can add an adapter without breaking your code.

---

## Core Concepts

### Hexagonal Architecture

Every module that interacts with external systems follows the ports and adapters pattern. Your services depend on `Protocol` contracts; concrete implementations are resolved by the DI container at startup.

```
┌──────────────────────────────────────────────┐
│              Your Application                 │
│                                              │
│   @service                 @repository       │
│   class OrderService:      class OrderRepo:  │
│       repo: RepositoryPort     ...           │
│       broker: MessageBrokerPort              │
│       cache: CacheAdapter                    │
│                                              │
│           Depends on PORTS (Protocols)        │
│                    │                         │
├────────────────────┼─────────────────────────┤
│                    │                         │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│   │SQLAlchemy│ │  Kafka   │ │  Redis   │   │
│   │ Adapter  │ │ Adapter  │ │ Adapter  │   │
│   └──────────┘ └──────────┘ └──────────┘   │
│                                              │
│           ADAPTERS (Implementations)         │
└──────────────────────────────────────────────┘
```

### Dependency Injection

PyFly's DI container uses **constructor injection** based on type hints — no annotations, no magic, just Python:

```python
@service
class OrderService:
    def __init__(self, repo: OrderRepository, events: EventPublisher) -> None:
        self._repo = repo
        self._events = events
```

The container inspects `__init__` parameters, resolves dependencies recursively, and manages bean lifecycles (singleton, transient, request-scoped).

### Auto-Configuration

PyFly detects installed libraries at startup and wires the appropriate adapters automatically. Redis installed? Cache uses `RedisCacheAdapter`. No broker library? Messaging uses `InMemoryMessageBroker`. You can always override with explicit configuration.

---

## Quick Start

```bash
# Install PyFly
bash install.sh

# Create a new project
pyfly new my-service

# Navigate and run
cd my-service
pyfly run --reload

# Visit the API docs
open http://localhost:8080/docs
```

See the [Getting Started Tutorial](getting-started.md) for a comprehensive walkthrough.

---

## Modules

PyFly is organized into four layers:

### Foundation Layer

| Module | Description | Guide |
|--------|-------------|-------|
| **Core** | Application bootstrap, lifecycle, banner, configuration | [Core & Lifecycle](guides/core.md) |
| **Kernel** | Exception hierarchy, structured error types | [Error Handling](guides/error-handling.md) |
| **Container** | Dependency injection, stereotypes, bean factories | [Dependency Injection](guides/dependency-injection.md) |
| **Context** | ApplicationContext, events, lifecycle hooks, conditions | [Dependency Injection](guides/dependency-injection.md) |

### Application Layer

| Module | Description | Guide |
|--------|-------------|-------|
| **Web** | HTTP routing, controllers, middleware, OpenAPI | [Web Layer](guides/web.md) |
| **Data** | Repository pattern, specifications, pagination | [Data Access](guides/data.md) |
| **CQRS** | Command/Query segregation with mediator | [CQRS](guides/cqrs.md) |
| **Validation** | Input validation with Pydantic | [Validation](guides/validation.md) |

### Infrastructure Layer

| Module | Description | Guide |
|--------|-------------|-------|
| **Security** | JWT, password encoding, authorization | [Security](guides/security.md) |
| **Messaging** | Kafka, RabbitMQ, in-memory broker | [Messaging](guides/messaging.md) |
| **EDA** | Event-driven architecture, event bus | [Events](guides/events.md) |
| **Cache** | Caching decorators, Redis adapter | [Caching](guides/caching.md) |
| **Client** | HTTP client, circuit breaker, retry | [HTTP Client](guides/client.md) |
| **Scheduling** | Cron jobs, fixed-rate tasks | [Scheduling](guides/scheduling.md) |
| **Resilience** | Rate limiter, bulkhead, timeout, fallback | [Resilience](guides/resilience.md) |

### Cross-Cutting Layer

| Module | Description | Guide |
|--------|-------------|-------|
| **AOP** | Aspect-oriented programming | [AOP](guides/aop.md) |
| **Observability** | Prometheus metrics, OpenTelemetry tracing | [Observability](guides/observability.md) |
| **Logging** | Structured logging with structlog | [Observability](guides/observability.md) |
| **Actuator** | Health checks, monitoring endpoints | [Actuator](guides/actuator.md) |
| **Testing** | Test fixtures and assertions | [Testing](guides/testing.md) |
| **CLI** | Command-line tools | [CLI Reference](cli.md) |

---

## Documentation

### Getting Started

- [Getting Started Tutorial](getting-started.md) — Build your first PyFly application step by step
- [Installation](installation.md) — Install and configure PyFly with the right extras
- [Architecture Overview](architecture.md) — Understand the framework's design and patterns

### Guides

- [Core & Lifecycle](guides/core.md) — Application bootstrap, configuration, profiles, banner
- [Dependency Injection](guides/dependency-injection.md) — Container, stereotypes, scopes, bean factories
- [Configuration](guides/configuration.md) — YAML config, profiles, property binding, environment variables
- [Error Handling](guides/error-handling.md) — Exception hierarchy, structured error responses
- [Web Layer](guides/web.md) — Controllers, routing, parameter binding, middleware, CORS, OpenAPI
- [Actuator](guides/actuator.md) — Health checks, beans, environment, info endpoints
- [Data Access](guides/data.md) — Repositories, derived queries, specifications, pagination
- [Messaging](guides/messaging.md) — Kafka, RabbitMQ, in-memory message broker
- [Events](guides/events.md) — Event-driven architecture, domain events, application events
- [CQRS](guides/cqrs.md) — Command/Query separation, mediator pattern
- [Security](guides/security.md) — JWT authentication, password encoding, authorization
- [Resilience](guides/resilience.md) — Rate limiting, bulkhead, timeout, fallback
- [HTTP Client](guides/client.md) — Service client, circuit breaker, retry
- [Caching](guides/caching.md) — Cache decorators, Redis adapter
- [Observability](guides/observability.md) — Metrics, tracing, health checks
- [Scheduling](guides/scheduling.md) — Cron jobs, fixed-rate/delay tasks
- [AOP](guides/aop.md) — Aspect-oriented programming, pointcuts, advice
- [Validation](guides/validation.md) — Input validation with Pydantic
- [Testing](guides/testing.md) — Test fixtures, assertions, mock containers

### Reference

- [Spring Boot Comparison](spring-comparison.md) — Side-by-side concept mapping for Java developers
- [CLI Reference](cli.md) — Command-line tools (new, run, db, info, doctor)

---

## Requirements

| Requirement | Version |
|-------------|---------|
| Python | >= 3.12 |
| pip | Latest recommended |
| OS | macOS, Linux (Windows support planned) |

See [Installation](installation.md) for optional dependencies and extras.

---

## License

Apache License 2.0 — Firefly Software Solutions Inc.
