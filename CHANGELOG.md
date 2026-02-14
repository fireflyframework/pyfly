# Changelog

All notable changes to PyFly will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## v0.1.0-alpha (2026-02-14) — Initial Release

The first public release of PyFly — the official native Python implementation of the [Firefly Framework](https://github.com/fireflyframework).

### Foundation Layer

- **`pyfly.kernel`** — Unified exception hierarchy with 25+ domain-specific error types, `ErrorResponse`, `ErrorCategory`, `ErrorSeverity`
- **`pyfly.core`** — Application bootstrap (`PyFlyApplication`, `@pyfly_application`), `Config` with YAML/TOML support, profile overlays, banner rendering
- **`pyfly.container`** — DI container with constructor injection, stereotype decorators (`@service`, `@component`, `@repository`, `@controller`, `@rest_controller`, `@configuration`), scopes (singleton, transient, request), `@bean`, `@primary`, `@order`, `Qualifier`
- **`pyfly.context`** — `ApplicationContext`, lifecycle hooks (`@post_construct`, `@pre_destroy`), `BeanPostProcessor`, conditions (`@conditional_on_property`, `@conditional_on_class`, `@conditional_on_bean`, `@conditional_on_missing_bean`), application events
- **`pyfly.config`** — `AutoConfigurationEngine` with provider detection for cache, messaging, HTTP client, and data subsystems
- **`pyfly.logging`** — `LoggingPort` and `StructlogAdapter` for structured logging

### Application Layer

- **`pyfly.web`** — HTTP routing (`@get_mapping`, `@post_mapping`, etc.), parameter binding (`Body`, `PathVar`, `QueryParam`, `Header`, `Cookie`), CORS, security headers, exception handling, Starlette/ASGI adapter
- **`pyfly.data`** — `RepositoryPort`, `SessionPort`, derived query methods (`@query`, `QueryMethodParser`), `Specification` pattern, `Page`/`Pageable`/`Sort`, `Mapper`, SQLAlchemy async adapter
- **`pyfly.cqrs`** — `Command`, `Query`, `CommandHandler`, `QueryHandler`, `Mediator`, logging and metrics middleware
- **`pyfly.validation`** — `@validate_input`, `@validator`, Pydantic model validation

### Infrastructure Layer

- **`pyfly.security`** — `JWTService`, `BcryptPasswordEncoder`, `SecurityContext`, `@secure`, `SecurityMiddleware`
- **`pyfly.messaging`** — `MessageBrokerPort`, `@message_listener`, adapters for Kafka (`aiokafka`), RabbitMQ (`aio-pika`), and in-memory
- **`pyfly.eda`** — `EventPublisher`, `EventEnvelope`, `@event_listener`, `@publish_result`, `InMemoryEventBus`, `ErrorStrategy`
- **`pyfly.cache`** — `CacheAdapter`, `CacheManager`, `@cacheable`, `@cache_evict`, `@cache_put`, Redis and in-memory adapters
- **`pyfly.client`** — `HttpClientPort`, `ServiceClient`, `CircuitBreaker`, `RetryPolicy`, declarative `@http_client`, HTTPX adapter
- **`pyfly.scheduling`** — `TaskExecutorPort`, `@scheduled`, `@async_method`, `CronExpression`, `TaskScheduler`, asyncio and thread pool executors
- **`pyfly.resilience`** — `@rate_limiter`, `@bulkhead`, `@time_limiter`, `@fallback`

### Cross-Cutting Layer

- **`pyfly.aop`** — `@aspect`, `@before`, `@after`, `@around`, `@after_returning`, `@after_throwing`, `AspectBeanPostProcessor`
- **`pyfly.observability`** — `@timed`, `@counted`, `@span`, `MetricsRegistry`, `HealthChecker`
- **`pyfly.actuator`** — Health, beans, environment, and info endpoints via `make_actuator_routes()`
- **`pyfly.testing`** — `PyFlyTestCase`, `create_test_container`, event assertions
- **`pyfly.cli`** — `pyfly new`, `pyfly run`, `pyfly info`, `pyfly doctor`, `pyfly db` (init, migrate, upgrade, downgrade)

### Tooling

- Interactive `install.sh` installer with venv creation, extras selection, and PATH configuration
- Non-interactive mode for CI/CD with environment variable overrides (`PYFLY_HOME`, `PYFLY_EXTRAS`)
