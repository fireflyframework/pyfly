<p align="center">
  <img src="../assets/pyfly-logo.png" alt="PyFly Logo" width="600" />
</p>

<p align="center">
  <strong>PyFly Framework Documentation</strong>
</p>

<p align="center">
  <em>Everything you need to build production-grade Python applications with PyFly.</em>
</p>

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

All module guides are organized in the [`guides/`](guides/README.md) directory. Here's a quick reference:

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
| [Validation](guides/validation.md) | `Valid[T]` annotation, Pydantic model validation, structured 422 errors |
| [WebFilters](guides/web-filters.md) | Request/response filter chain — `TransactionIdFilter`, `RequestLoggingFilter`, `SecurityHeadersFilter` |
| [Actuator](guides/actuator.md) | Health checks, beans endpoint, environment info, loggers, metrics |
| [Custom Actuator Endpoints](guides/custom-actuator-endpoints.md) | Build your own actuator endpoints with the `ActuatorEndpoint` protocol |

### Data & Persistence

| Guide | Description |
|-------|-------------|
| [Data Access (SQL)](guides/data.md) | Repositories, derived queries, specifications, pagination, transactions (SQLAlchemy) |
| [MongoDB](guides/mongodb.md) | Document database support via Beanie ODM — `MongoRepository[T, ID]`, `BaseDocument`, derived queries |

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
- **Setting up a SQL database?** See the [Data Access Guide](guides/data.md)
- **Setting up MongoDB?** See the [MongoDB Guide](guides/mongodb.md)
- **Need messaging?** See [Messaging](guides/messaging.md) and [Events](guides/events.md)
- **Browse all guides:** See the [Guides Index](guides/README.md)
