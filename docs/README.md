# PyFly Documentation

Welcome to the PyFly Framework documentation. This is your starting point for learning how to build enterprise-grade Python applications with PyFly.

---

## Getting Started

| Guide | Description |
|-------|-------------|
| [Introduction](index.md) | What is PyFly, philosophy, and why use it |
| [Installation](installation.md) | Install PyFly with the interactive installer or pip |
| [Getting Started Tutorial](getting-started.md) | Build your first PyFly application step by step |
| [Architecture Overview](architecture.md) | Understand the framework's hexagonal design and module layers |

---

## Framework Guides

### Foundation

| Guide | Description |
|-------|-------------|
| [Core & Lifecycle](guides/core.md) | Application bootstrap, startup sequence, configuration, profiles, banner |
| [Dependency Injection](guides/dependency-injection.md) | Container, stereotypes, scopes, bean factories, conditional beans, lifecycle hooks |
| [Configuration](guides/configuration.md) | YAML/TOML config, profiles, property binding, environment variables |
| [Error Handling](guides/error-handling.md) | Exception hierarchy, HTTP status mapping, structured error responses |

### Web Development

| Guide | Description |
|-------|-------------|
| [Web Layer](guides/web.md) | REST controllers, routing, parameter binding, middleware, CORS, OpenAPI |
| [Actuator](guides/actuator.md) | Health checks, beans endpoint, environment info, application metadata |

### Data & Persistence

| Guide | Description |
|-------|-------------|
| [Data Access](guides/data.md) | Repositories, derived queries, specifications, pagination, transactions |

### Messaging & Events

| Guide | Description |
|-------|-------------|
| [Messaging](guides/messaging.md) | Kafka, RabbitMQ, in-memory broker, message publishing and consumption |
| [Events (EDA)](guides/events.md) | Event-driven architecture, domain events, application events, event bus |
| [CQRS](guides/cqrs.md) | Command/Query separation, mediator pattern, middleware pipeline |

### Security

| Guide | Description |
|-------|-------------|
| [Security](guides/security.md) | JWT authentication, password encoding, authorization, protected endpoints |

### Resilience & Performance

| Guide | Description |
|-------|-------------|
| [Resilience](guides/resilience.md) | Rate limiting, bulkhead, timeout, fallback patterns |
| [HTTP Client](guides/client.md) | Service client builder, circuit breaker, retry, declarative clients |
| [Caching](guides/caching.md) | Cache decorators, Redis adapter, in-memory cache, cache management |

### Operations

| Guide | Description |
|-------|-------------|
| [Observability](guides/observability.md) | Prometheus metrics, OpenTelemetry tracing, structured logging, health checks |
| [Scheduling](guides/scheduling.md) | Cron jobs, fixed-rate tasks, fixed-delay tasks, async execution |

### Advanced

| Guide | Description |
|-------|-------------|
| [AOP](guides/aop.md) | Aspect-oriented programming, pointcuts, advice types, weaving |
| [Validation](guides/validation.md) | Pydantic model validation, custom validators, input validation decorators |
| [Testing](guides/testing.md) | Test fixtures, mock containers, event assertions, testing patterns |

---

## Reference

| Document | Description |
|----------|-------------|
| [CLI Reference](cli.md) | Command-line tools — `new`, `run`, `info`, `doctor`, `db` |
| [Spring Boot Comparison](spring-comparison.md) | Side-by-side concept mapping for Java developers |

---

## Quick Links

- **New to PyFly?** Start with the [Getting Started Tutorial](getting-started.md)
- **Coming from Spring Boot?** Read the [Spring Boot Comparison](spring-comparison.md)
- **Building a web service?** See the [Web Layer Guide](guides/web.md)
- **Setting up a database?** See the [Data Access Guide](guides/data.md)
- **Need messaging?** See [Messaging](guides/messaging.md) and [Events](guides/events.md)
