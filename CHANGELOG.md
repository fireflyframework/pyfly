# Changelog

All notable changes to PyFly will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## v0.1.0-alpha.5 (2026-02-17)

### Added

- **Transactional engine** (`pyfly.transactional`) — Full port of `fireflyframework-transactional-engine` (Java/Spring Boot) to Python/asyncio. Implements two distributed transaction patterns:
  - **SAGA pattern** — `@saga` and `@saga_step` decorators with DAG-based topological execution, 5 compensation policies (STRICT_SEQUENTIAL, GROUPED_PARALLEL, RETRY_WITH_BACKOFF, CIRCUIT_BREAKER, BEST_EFFORT_PARALLEL), parameter injection via `typing.Annotated` markers (`Input`, `FromStep`, `Header`, `Variable`, `SetVariable`, `FromCompensationResult`, `CompensationError`), retry with exponential backoff and jitter, step timeout via `asyncio.wait_for`, layer concurrency via `asyncio.Semaphore`
  - **TCC pattern** — `@tcc` and `@tcc_participant` decorators with `@try_method`, `@confirm_method`, `@cancel_method` for three-phase Try-Confirm-Cancel transactions, participant ordering, timeout and retry support
  - **Saga composition** — `SagaCompositionBuilder` fluent DSL for orchestrating multiple sagas into a DAG with cross-saga data flow and compensation management
  - **Persistence** — `TransactionalPersistencePort` protocol with `InMemoryPersistenceAdapter` default, state tracking for saga and TCC executions, recovery service for stale/in-flight sagas
  - **Observability** — `TransactionalEventsPort` protocol with `LoggerEventsAdapter` and `CompositeEventsAdapter`
  - **Backpressure** — `BackpressureStrategyPort` protocol with 3 strategies: `AdaptiveBackpressureStrategy`, `BatchedBackpressureStrategy`, `CircuitBreakerBackpressureStrategy`
  - **Compensation error handling** — `CompensationErrorHandlerPort` protocol with 4 handlers: `FailFastHandler`, `LogAndContinueHandler`, `RetryWithBackoffHandler`, `CompositeCompensationErrorHandler`
  - **Auto-configuration** — `TransactionalEngineAutoConfiguration` with 14 `@bean` factory methods, enabled via `pyfly.transactional.enabled=true`
  - **681 tests** including end-to-end integration tests

---

## v0.1.0-alpha.4 (2026-02-17)

### Added

- **Admin dashboard** (`pyfly.admin`) — Spring Boot Admin-inspired embedded management dashboard for monitoring PyFly applications at runtime. 14 built-in views: Overview, Health, Beans, Environment, Configuration, Loggers, Metrics, Scheduled Tasks, HTTP Traces, Mappings, Caches, CQRS, Log Viewer, and Instances (server mode). Real-time SSE updates for health, metrics, and traces (`/admin/api/sse/*`). Server mode with `InstanceRegistry` and `StaticDiscovery` for multi-instance fleet monitoring. Client registration for auto-announcing to a remote admin server. Extensible via `AdminViewExtension` protocol for custom views. Zero-build vanilla JavaScript SPA frontend served from `pyfly.admin.static`. No additional dependencies beyond `pyfly[web]`. Enable with `pyfly.admin.enabled: true`
- **CLI archetype** (`pyfly new --archetype cli`) — New scaffolding archetype for command-line applications. Generates `@shell_component` commands, `@service` business logic, non-ASGI `main.py` entry point, and shell-enabled `pyfly.yaml`. Includes `shell` feature in the feature system with `FEATURE_GROUPS`, `FEATURE_DETAILS`, and `FEATURE_TIPS` entries
- **Shell subsystem** (`pyfly.shell`) — Spring Shell-inspired CLI framework with full DI integration. `@shell_component` stereotype for command classes, `@shell_method` for command declarations, `@shell_option` / `@shell_argument` for explicit parameter overrides. Automatic parameter inference from type hints (positional args, `--options`, `--flags`). `ShellRunnerPort` protocol with `ClickShellAdapter` (Click 8.1+). `CommandLineRunner` and `ApplicationRunner` protocols for post-startup hooks. `ApplicationArguments` for parsed CLI argument access. `ShellAutoConfiguration` via `pyfly.auto_configuration` entry point (enabled with `pyfly.shell.enabled=true`). Install via `pip install pyfly[shell]`

### Changed

- **Decentralized auto-configuration** — `AutoConfigurationEngine` has been removed. Each subsystem now owns its own `@auto_configuration` class (e.g. `CacheAutoConfiguration`, `MessagingAutoConfiguration`, `WebAutoConfiguration`, `RelationalAutoConfiguration`, `DocumentAutoConfiguration`, `ClientAutoConfiguration`). The central `AutoConfigurationEngine.configure()` call is replaced by `discover_auto_configurations()` which discovers `@auto_configuration` classes via the `pyfly.auto_configuration` entry-point group. Third-party packages can register their own auto-configuration classes through the same mechanism. Provider detection (`detect_provider()`) now lives inside each subsystem's auto-configuration class; the core `AutoConfiguration` class only exposes the generic `is_available()` helper
- **`ApplicationContext` Beanie initialization** — `_initialize_beanie()` has been removed from `ApplicationContext`. Beanie ODM initialization is now handled by `BeanieInitializer`, a lifecycle bean registered by `DocumentAutoConfiguration`
- **`SecurityMiddleware` relocated** — Canonical location moved from `pyfly.security` to `pyfly.web.adapters.starlette.security_middleware`. JWT enforcement is now handled by `SecurityFilter` (a `WebFilter` in the filter chain); `SecurityMiddleware` is retained as a `BaseHTTPMiddleware` for backward compatibility
- **`ServiceClient` class removed** — The `pyfly.client.service_client` module (containing the `ServiceClient` class) has been deleted. The `@service_client` decorator remains available in `pyfly.client.declarative` and is exported from `pyfly.client`. HTTP client functionality is provided by the declarative `@http_client` / `@service_client` interface and `HttpClientPort` adapter
- **`pyfly.observability` consolidated** — `pyfly.observability.health` and `pyfly.observability.logging` removed; health and logging concerns are handled by `pyfly.actuator` and `pyfly.logging` respectively
- **`pyfly.cache.types` removed** — Cache type definitions consolidated into `pyfly.cache` package exports

---

## v0.1.0-alpha.3 (2026-02-15)

### Added

- **Spring Data umbrella refactoring** — `pyfly.data` is now a pure commons layer (Page, Pageable, ports, QueryMethodParser). Relational modules moved to `pyfly.data.relational` (Specification, Filter, Query, SQLAlchemy adapter). Document modules moved to `pyfly.data.document` (MongoDB/Beanie adapter). Config prefixes changed to `pyfly.data.relational.*` and `pyfly.data.document.*`. Feature names renamed to `data-relational` and `data-document`. Properties renamed to `RelationalProperties` and `DocumentProperties`
- **MongoDB/Document Database Support** (`pyfly.data.document.mongodb`) — `MongoRepository[T, ID]`, `BaseDocument`, `MongoQueryMethodCompiler`, `MongoRepositoryBeanPostProcessor`, `mongo_transactional`. Install via `pip install pyfly[data-document]`. Beanie ODM initialization is handled by `BeanieInitializer` lifecycle bean (registered by `DocumentAutoConfiguration` in alpha.4)
- `DocumentProperties` configuration (`pyfly.data.document.*` — uri, database, pool sizes)
- Auto-detection of Beanie ODM via `AutoConfiguration.detect_document_provider()` [Superseded in alpha.4: detection now handled by `DocumentAutoConfiguration` registered via `@auto_configuration`]
- CLI scaffolding: `--features data-document` generates Beanie documents, MongoRepository, and MongoDB config. Both `data-relational` and `data-document` can be selected together for multi-backend projects
- Derived query method compilation for MongoDB (reuses shared `QueryMethodParser` + `MongoQueryMethodCompiler`)
- New documentation guide: `docs/guides/data-document.md`
- **Generic repository IDs** — `RepositoryPort[T, ID]` and `Repository[T, ID]` are now dual-generic, accepting any primary key type (UUID, int, str). `CrudRepository[T, ID]` and `PagingRepository[T, ID]` were already dual-generic
- **CLI wizard revamp** — Interactive `pyfly new` wizard now uses 4 numbered steps with archetype comparison table, grouped feature selection with `questionary.Separator`, and feature-aware post-generation tips
- **Feature-aware scaffolding** — Templates generate code based on selected features: `Valid[T]` in controllers (replaces `Body[T]`), `Field()` constraints in models, conditional SQLAlchemy `Repository[ItemEntity, int]` (with `data-relational` feature) vs in-memory store, actuator config, `adapter: auto` in pyfly.yaml

### Changed

- **`RepositoryPort`** — **Breaking:** Now `RepositoryPort[T, ID]` instead of `RepositoryPort[T]`. Existing code using `RepositoryPort[MyEntity]` must change to `RepositoryPort[MyEntity, UUID]` (or appropriate ID type)
- **`Repository`** — **Breaking:** Now `Repository[T, ID]` instead of `Repository[T]`. Existing code using `Repository[MyEntity]` must change to `Repository[MyEntity, UUID]` (or appropriate ID type). `bound=BaseEntity` constraint removed — any SQLAlchemy model works
- **Scaffolded controllers** — Now use `Valid[T]` instead of `Body[T]` for structured 422 error responses
- **Scaffolded models** — Now include `Field(min_length=..., max_length=...)` constraints and conditional `ItemEntity(Base)` when data feature is selected
- **Scaffolded pyfly.yaml** — Now includes `adapter: auto` under `web:` and `actuator: endpoints: enabled: true` for non-library archetypes

### Added

- **`Valid[T]` annotation** (`pyfly.web.params`) — Explicit parameter validation marker for controller handlers. `Valid[T]` standalone implies `Body[T]` + structured 422 errors; `Valid[Body[T]]` and `Valid[QueryParam[T]]` wrap inner binding types. Catches Pydantic `ValidationError` and converts to `ValidationException` with `code="VALIDATION_ERROR"` and `context={"errors": [...]}`
- **Config-driven web adapter selection** — New `pyfly.web.adapter` config key (`auto|starlette`). `AutoConfiguration.detect_web_adapter()` checks if Starlette is importable. `AutoConfigurationEngine._configure_web()` registers `StarletteWebAdapter` as a `WebServerPort` bean [Superseded in alpha.4: `AutoConfigurationEngine` removed; web adapter registration now handled by `WebAutoConfiguration` via `@auto_configuration` and entry-point discovery]
- **`StarletteWebAdapter`** — Class-based `WebServerPort` implementation that delegates to `create_app()`, registered via auto-configuration
- **WebFilter chain architecture** — `WebFilterChainMiddleware` wraps all `WebFilter` instances into a single Starlette middleware. Built-in filters: `TransactionIdFilter`, `RequestLoggingFilter`, `SecurityHeadersFilter`, `SecurityFilter`. User filters auto-discovered from DI context
- **`OncePerRequestFilter`** base class — URL-pattern matching via `url_patterns` and `exclude_patterns` (fnmatch globs)
- **`ActuatorEndpoint` protocol** — Extensible actuator endpoint interface with `endpoint_id`, `enabled`, and `handle()`. Custom endpoints auto-discovered from DI container
- **`ActuatorRegistry`** — Collects and manages actuator endpoints with per-endpoint enable/disable via `pyfly.actuator.endpoints.{id}.enabled` config
- **`/actuator` index endpoint** — HAL-style `_links` response listing all enabled endpoints
- **`LoggersEndpoint`** — `GET /actuator/loggers` lists all loggers; `POST /actuator/loggers` changes log levels at runtime
- **`MetricsEndpoint`** — Stub endpoint at `/actuator/metrics` (disabled by default) for future Prometheus/OpenTelemetry integration
- **New documentation guides** — `web-filters.md` (WebFilter chain reference), `custom-actuator-endpoints.md` (extensible actuator guide)

### Changed

- **`WebProperties`** — Added `adapter: str = "auto"` field for config-driven web adapter selection
- **`ParameterResolver`** — `ResolvedParam` dataclass gains `validate: bool` field; resolver inspects and unwraps `Valid[T]` annotations during parameter inspection and resolution
- **`ControllerRegistrar`** — `_extract_param_metadata()` now unwraps `Valid[T]` for correct OpenAPI spec generation
- **`AutoConfigurationEngine.configure()`** — Now calls `_configure_web()` before other subsystem configurations [Superseded in alpha.4: `AutoConfigurationEngine` removed; replaced by `discover_auto_configurations()` with per-subsystem `@auto_configuration` classes]

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
- **Auto-configuration engine** — Tracks created adapters for lifecycle management; validation moved from socket-level checks to adapter `start()` methods [Superseded in alpha.4: centralized engine removed; each subsystem's `@auto_configuration` class manages its own adapter lifecycle]
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
- **`pyfly.config`** — `AutoConfiguration` utility with provider detection helpers, `discover_auto_configurations()` entry-point discovery [Superseded in alpha.4: `AutoConfigurationEngine` removed; provider detection remains in `AutoConfiguration`, but subsystem registration is now handled by per-subsystem `@auto_configuration` classes discovered via entry points]
- **`pyfly.logging`** — `LoggingPort` and `StructlogAdapter` for structured logging

### Application Layer

- **`pyfly.web`** — HTTP routing (`@get_mapping`, `@post_mapping`, etc.), parameter binding (`Body`, `PathVar`, `QueryParam`, `Header`, `Cookie`), CORS, security headers, exception handling, Starlette/ASGI adapter
- **`pyfly.data`** — `RepositoryPort`, `SessionPort`, derived query methods (`QueryMethodParser`), `Specification` pattern, `Page`/`Pageable`/`Sort`, `Mapper`, SQLAlchemy async adapter. The `@query` decorator lives in `pyfly.data.relational.sqlalchemy.query`
- **`pyfly.cqrs`** — `Command`, `Query`, `CommandHandler`, `QueryHandler`, `Mediator`, logging and metrics middleware
- **`pyfly.validation`** — `@validate_input`, `@validator`, Pydantic model validation

### Infrastructure Layer

- **`pyfly.security`** — `JWTService`, `BcryptPasswordEncoder`, `SecurityContext`, `@secure`, `SecurityMiddleware` [Superseded in alpha.4: `SecurityMiddleware` relocated to `pyfly.web.adapters.starlette.security_middleware` and integrated as a `WebFilter`]
- **`pyfly.messaging`** — `MessageBrokerPort`, `@message_listener`, adapters for Kafka (`aiokafka`), RabbitMQ (`aio-pika`), and in-memory
- **`pyfly.eda`** — `EventPublisher`, `EventEnvelope`, `@event_listener`, `@publish_result`, `InMemoryEventBus`, `ErrorStrategy`
- **`pyfly.cache`** — `CacheAdapter`, `CacheManager`, `@cacheable`, `@cache_evict`, `@cache_put`, Redis and in-memory adapters
- **`pyfly.client`** — `HttpClientPort`, `ServiceClient`, `CircuitBreaker`, `RetryPolicy`, declarative `@http_client`, HTTPX adapter
- **`pyfly.scheduling`** — `TaskExecutorPort`, `@scheduled`, `@async_method`, `CronExpression`, `TaskScheduler`, asyncio and thread pool executors
- **`pyfly.resilience`** — `@rate_limiter`, `@bulkhead`, `@time_limiter`, `@fallback`

### Cross-Cutting Layer

- **`pyfly.aop`** — `@aspect`, `@before`, `@after`, `@around`, `@after_returning`, `@after_throwing`, `AspectBeanPostProcessor`
- **`pyfly.observability`** — `@timed`, `@counted`, `@span`, `MetricsRegistry`
- **`pyfly.actuator`** — Health, beans, environment, and info endpoints via `ActuatorEndpoint` protocol and `ActuatorRegistry`
- **`pyfly.testing`** — `PyFlyTestCase`, `create_test_container`, event assertions
- **`pyfly.cli`** — `pyfly new`, `pyfly run`, `pyfly info`, `pyfly doctor`, `pyfly db` (init, migrate, upgrade, downgrade), `pyfly license`, `pyfly sbom`

### Tooling

- Interactive `install.sh` installer with venv creation, extras selection, and PATH configuration
- Non-interactive mode for CI/CD with environment variable overrides (`PYFLY_HOME`, `PYFLY_EXTRAS`)
