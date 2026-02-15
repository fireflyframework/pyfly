# Changelog

All notable changes to PyFly will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## v0.1.0-alpha.2 (2026-02-15)

### Added

- **Unified Lifecycle protocol** (`pyfly.kernel.Lifecycle`) — All infrastructure adapters now implement a standard `start()`/`stop()` contract for connection management and resource cleanup
- **Fail-fast startup** — If explicitly configured infrastructure (Redis, Kafka, RabbitMQ, etc.) is unreachable, the application fails immediately with `BeanCreationException` instead of starting in a broken state
- **Multi-source config loading** (`Config.from_sources()`) — Auto-discovers and loads config files from a directory with source tracking via `loaded_sources` property
- **Config source logging** — Startup now logs which configuration sources were loaded (framework defaults, user config, profile overlays)
- **Route and API docs logging** — Startup logs mapped HTTP endpoints and API documentation URLs (Swagger UI, ReDoc, OpenAPI)
- **Interactive CLI wizard** (`pyfly new`) — Arrow-key archetype selection and space-bar feature toggling via questionary, with Rich-styled confirmation summary
- **Graceful Ctrl+C handling** — Interactive wizard exits cleanly without traceback on keyboard interrupt

### Changed

- **Port lifecycle standardization** — All infrastructure ports (`HttpClientPort`, `CacheAdapter`, `TaskExecutorPort`, `EventPublisher`) now use `start()`/`stop()` instead of `close()`/`shutdown()`
- **ServiceClient** — `close()` renamed to `stop()`, added `start()` for lifecycle symmetry
- **TaskScheduler.stop()** — No longer accepts `wait` parameter; always performs graceful shutdown
- **BeanCreationException** — Now inherits from `InfrastructureException` (was `Exception`)
- **Auto-configuration engine** — Tracks created adapters for lifecycle management; validation moved from socket-level checks to adapter `start()` methods
- **Startup sequence** — Added adapter lifecycle phase: infrastructure adapters are started after auto-configuration and stopped in reverse order during shutdown
- **Scan logging deferred** — Package scan results now appear after the banner, not before
- **Uvicorn noise suppressed** — Redundant startup/shutdown messages from uvicorn are suppressed

### Fixed

- **Config key alignment** — Scaffolding templates now use correct `pyfly.*` config keys matching framework defaults
- **Framework defaults** — Default providers set to `memory` (not `auto`) so apps start without external infrastructure

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
