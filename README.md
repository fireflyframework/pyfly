# PyFly Framework

**The Enterprise Python Framework**

> *Build production-grade applications with the patterns you trust — dependency injection, CQRS, event-driven architecture, and more — all native to Python.*

---

## What is PyFly?

PyFly is a comprehensive application framework for Python 3.12+ that brings well-established enterprise patterns to the Python ecosystem. It provides a **cohesive programming model** for building production-grade microservices, monoliths, and libraries — while embracing Python's strengths: `async/await`, type hints, protocols, and simplicity.

Rather than wiring together dozens of independent libraries for each new project, PyFly gives you an opinionated, full-stack foundation where every module is designed to work together seamlessly.

### Who is PyFly for?

- **Teams migrating from Java/Spring** who want familiar concepts expressed natively in Python
- **Python developers** who want enterprise-grade patterns without reinventing the wheel
- **Architects** building microservice platforms who need consistency across services
- **Anyone** tired of choosing from hundreds of libraries and assembling them from scratch

If you're coming from Spring Boot, check out our [Spring Boot Comparison Guide](docs/spring-comparison.md) for a detailed mapping of concepts.

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
curl -fsSL https://raw.githubusercontent.com/your-org/pyfly/main/install.sh | bash

# Create a new project
pyfly new my-service

# Navigate and run
cd my-service
pyfly run --reload

# Visit the API docs
open http://localhost:8080/docs
```

See the [Getting Started Tutorial](docs/getting-started.md) for a comprehensive walkthrough.

---

## Modules

PyFly is organized into four layers:

### Foundation Layer

| Module | Description |
|--------|-------------|
| **Core** | Application bootstrap, lifecycle, banner, configuration |
| **Kernel** | Exception hierarchy, structured error types |
| **Container** | Dependency injection, stereotypes, bean factories |
| **Context** | ApplicationContext, events, lifecycle hooks, conditions |

### Application Layer

| Module | Description |
|--------|-------------|
| **Web** | HTTP routing, controllers, middleware, OpenAPI |
| **Data** | Repository pattern, specifications, pagination |
| **CQRS** | Command/Query segregation with mediator |
| **Validation** | Input validation with Pydantic |

### Infrastructure Layer

| Module | Description |
|--------|-------------|
| **Security** | JWT, password encoding, authorization |
| **Messaging** | Kafka, RabbitMQ, in-memory broker |
| **EDA** | Event-driven architecture, event bus |
| **Cache** | Caching decorators, Redis adapter |
| **Client** | HTTP client, circuit breaker, retry |
| **Scheduling** | Cron jobs, fixed-rate tasks |
| **Resilience** | Rate limiter, bulkhead, timeout, fallback |

### Cross-Cutting Layer

| Module | Description |
|--------|-------------|
| **AOP** | Aspect-oriented programming |
| **Observability** | Prometheus metrics, OpenTelemetry tracing |
| **Logging** | Structured logging with structlog |
| **Actuator** | Health checks, monitoring endpoints |
| **Testing** | Test fixtures and assertions |
| **CLI** | Command-line tools |

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

## Requirements

| Requirement | Version |
|-------------|---------|
| Python | >= 3.12 |
| pip | Latest recommended |
| OS | macOS, Linux (Windows support planned) |

---

## License

Apache License 2.0 — Firefly Software Solutions Inc.
