# Architecture Overview

This document describes the architectural vision, module organization, design decisions,
and internal mechanics of the PyFly framework. It is intended for contributors,
advanced users, and anyone who wants to understand *why* PyFly is structured the way it is.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Architectural Vision](#architectural-vision)
3. [Hexagonal Architecture: Ports and Adapters](#hexagonal-architecture-ports-and-adapters)
   - [What Are Ports?](#what-are-ports)
   - [What Are Adapters?](#what-are-adapters)
   - [Hexagonal Diagram](#hexagonal-diagram)
4. [Module Layer Organization](#module-layer-organization)
   - [Foundation Layer](#foundation-layer)
   - [Application Layer](#application-layer)
   - [Infrastructure Layer](#infrastructure-layer)
   - [Cross-Cutting Layer](#cross-cutting-layer)
   - [Layer Diagram](#layer-diagram)
5. [The Startup Sequence in Detail](#the-startup-sequence-in-detail)
   - [Phase 1: PyFlyApplication Constructor](#phase-1-pyflyapplication-constructor)
   - [Phase 2: startup()](#phase-2-startup)
   - [Phase 3: ApplicationContext.start()](#phase-3-applicationcontextstart)
   - [Complete Startup Flow Diagram](#complete-startup-flow-diagram)
6. [Dependency Injection Architecture](#dependency-injection-architecture)
   - [Container vs ApplicationContext](#container-vs-applicationcontext)
   - [Registration and Resolution](#registration-and-resolution)
   - [Stereotype System](#stereotype-system)
7. [Auto-Configuration](#auto-configuration)
   - [Declarative Auto-Configuration](#declarative-auto-configuration)
   - [Imperative Auto-Configuration](#imperative-auto-configuration)
   - [Provider Detection](#provider-detection)
8. [Framework-Agnostic Design](#framework-agnostic-design)
   - [Web Module](#web-module)
   - [Data Module](#data-module)
   - [Messaging Module](#messaging-module)
   - [Cache Module](#cache-module)
   - [Scheduling Module](#scheduling-module)
9. [Configuration Architecture](#configuration-architecture)
10. [Event-Driven Design](#event-driven-design)
    - [Application Events](#application-events)
    - [Domain Events (EDA)](#domain-events-eda)
11. [Cross-Cutting Concerns](#cross-cutting-concerns)
    - [Aspect-Oriented Programming](#aspect-oriented-programming)
    - [Observability](#observability)
    - [Resilience](#resilience)
    - [Security](#security)
    - [Validation](#validation)
12. [Design Decisions and Trade-Offs](#design-decisions-and-trade-offs)

---

## Introduction

PyFly is an enterprise Python framework that brings the architectural patterns of
Spring Boot to the Python ecosystem while remaining Pythonic, async-first, and
lightweight. It provides a comprehensive foundation for building production-grade
applications with dependency injection, configuration management, web serving, data
access, messaging, caching, security, observability, and more.

The framework is organized around two key architectural ideas:

1. **Hexagonal (ports-and-adapters) architecture** at the module level.
2. **Layered module organization** that enforces dependency direction.

---

## Architectural Vision

PyFly's vision is to let application developers focus on business logic while the
framework handles infrastructure concerns. The guiding principles are:

- **Convention over configuration**: sensible defaults for everything; override only
  what differs.
- **Dependency inversion**: application code depends on ports (interfaces), not on
  infrastructure details.
- **Framework-agnostic abstractions**: swap web frameworks, databases, message brokers,
  or cache backends without touching business logic.
- **Async-first**: all I/O-bound operations use `async`/`await` natively.
- **Testability**: constructor injection and interface binding make every component
  independently testable.

---

## Hexagonal Architecture: Ports and Adapters

PyFly implements hexagonal architecture (also called ports and adapters) at the module
level. Every infrastructure-facing module separates its abstract contracts from
concrete implementations.

### What Are Ports?

Ports are abstract contracts (Python `Protocol` classes or ABCs) that define what
the application needs without specifying how. They live in `ports/` subdirectories
within each module.

Examples of ports in the framework:

| Port | Module | Purpose |
|---|---|---|
| `RepositoryPort` | `pyfly.data.ports.outbound` | Defines data access operations (save, find, delete). |
| `SessionPort` | `pyfly.data.ports.outbound` | Defines database session operations. |
| `MessageBrokerPort` | `pyfly.messaging.ports.outbound` | Defines message publishing and subscribing. |
| `CacheAdapter` | `pyfly.cache.ports.outbound` | Defines cache get/set/delete operations. |
| `HttpClientPort` | `pyfly.client.ports.outbound` | Defines HTTP request operations. |
| `TaskExecutorPort` | `pyfly.scheduling.ports.outbound` | Defines task execution. |
| `LoggingPort` | `pyfly.logging` | Defines structured logging operations. |

### What Are Adapters?

Adapters are concrete implementations of ports, bound to a specific technology. They
live in `adapters/` subdirectories within each module.

Examples of adapters:

| Adapter | Module | Implements | Technology |
|---|---|---|---|
| `Repository` | `pyfly.data.relational.sqlalchemy` | `RepositoryPort` | SQLAlchemy |
| `KafkaAdapter` | `pyfly.messaging.adapters.kafka` | `MessageBrokerPort` | aiokafka |
| `RabbitMQAdapter` | `pyfly.messaging.adapters.rabbitmq` | `MessageBrokerPort` | aio_pika |
| `InMemoryMessageBroker` | `pyfly.messaging.adapters.memory` | `MessageBrokerPort` | In-process |
| `RedisCacheAdapter` | `pyfly.cache.adapters.redis` | `CacheAdapter` | redis.asyncio |
| `InMemoryCache` | `pyfly.cache.adapters.memory` | `CacheAdapter` | In-process dict |
| `HttpxClientAdapter` | `pyfly.client.adapters.httpx_adapter` | `HttpClientPort` | HTTPX |
| `ControllerRegistrar` | `pyfly.web.adapters.starlette` | Web routing | Starlette/ASGI |
| `AsyncIOTaskExecutor` | `pyfly.scheduling.adapters.asyncio_executor` | `TaskExecutorPort` | asyncio |
| `ThreadPoolTaskExecutor` | `pyfly.scheduling.adapters.thread_executor` | `TaskExecutorPort` | concurrent.futures |
| `StructlogAdapter` | `pyfly.logging` | `LoggingPort` | structlog |

### Hexagonal Diagram

```
                     +-------------------------------------------+
                     |           Application Core                |
                     |                                           |
                     |   @service    @repository   @component    |
                     |   Business logic, domain models           |
                     |                                           |
                     +------+----+---------+----+--------+-------+
                            |    |         |    |        |
                     +------v-+  |  +------v-+  |  +-----v------+
                     | Port   |  |  | Port   |  |  | Port       |
                     | Data   |  |  | Cache  |  |  | Messaging  |
                     +------+-+  |  +------+-+  |  +-----+------+
                            |    |         |    |        |
               +------------v-+  |  +------v--+ |  +-----v--------+
               | Adapter      |  |  | Adapter | |  | Adapter      |
               | SQLAlchemy   |  |  | Redis   | |  | Kafka        |
               +--------------+  |  +---------+ |  +--------------+
                                 |
                          +------v-------+
                          | Adapter      |
                          | Starlette    |
                          +--------------+
```

Application code depends only on ports. Adapters are wired at startup through DI container
bindings or auto-configuration. Swapping an adapter (e.g., from Redis to Memcached)
requires only changing a binding -- no business logic changes.

---

## Unified Lifecycle Protocol

All infrastructure adapters implement the `Lifecycle` protocol from `pyfly.kernel`:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Lifecycle(Protocol):
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
```

This provides a standard contract for managing infrastructure connections:

- **`start()`** — Initialize connections, validate connectivity (e.g., Redis `PING`, Kafka broker connect). Called during application startup.
- **`stop()`** — Release resources, close connections. Called during application shutdown in reverse order.

All port protocols include `start()` and `stop()` alongside their domain methods:

| Port | Domain Methods | Lifecycle |
|---|---|---|
| `MessageBrokerPort` | `publish()`, `subscribe()` | `start()`, `stop()` |
| `CacheAdapter` | `get()`, `put()`, `evict()`, `exists()`, `clear()` | `start()`, `stop()` |
| `HttpClientPort` | `request()` | `start()`, `stop()` |
| `TaskExecutorPort` | `submit()` | `start()`, `stop()` |
| `EventPublisher` | `publish()`, `subscribe()` | `start()`, `stop()` |

This unified lifecycle enables:
- **Fail-fast startup**: adapters validate connectivity in `start()`, failing immediately if infrastructure is unreachable.
- **Graceful shutdown**: adapters release resources in `stop()`, called in reverse initialization order.
- **Consistent testing**: mock adapters implement the same `start()`/`stop()` contract.

---

## Module Layer Organization

PyFly's modules are organized into four layers. Dependencies flow downward only: higher
layers may depend on lower layers, but never the reverse.

### Foundation Layer

The foundation provides primitives with zero or minimal external dependencies.

| Module | Package | Purpose |
|---|---|---|
| **Kernel** | `pyfly.kernel` | Exception hierarchy (`PyFlyException` and 25+ domain-specific subclasses), error types (`ErrorResponse`, `ErrorCategory`, `ErrorSeverity`, `FieldError`), `Lifecycle` protocol for unified adapter lifecycle. Zero external dependencies. |
| **Core** | `pyfly.core` | Application bootstrap (`PyFlyApplication`, `@pyfly_application`), configuration (`Config`, `@config_properties`), and banner rendering (`BannerPrinter`, `BannerMode`). |
| **Container** | `pyfly.container` | DI container (`Container`), stereotypes (`@service`, `@component`, `@repository`, `@controller`, `@rest_controller`, `@configuration`), scopes (`Scope`), `@bean`, `@primary`, `@order`, `Qualifier`, component scanning. |
| **Context** | `pyfly.context` | `ApplicationContext`, lifecycle hooks (`@post_construct`, `@pre_destroy`), `BeanPostProcessor` protocol, conditions (`@conditional_on_property`, `@conditional_on_class`, `@conditional_on_bean`, `@conditional_on_missing_bean`), events (`ApplicationReadyEvent`, `ContextRefreshedEvent`, `ContextClosedEvent`, `@app_event_listener`), `Environment`. |
| **Config** | `pyfly.config` | Auto-configuration engine (`AutoConfiguration`, `AutoConfigurationEngine`). Provider detection and imperative adapter wiring. |
| **Logging** | `pyfly.logging` | Logging port (`LoggingPort`) and structlog adapter (`StructlogAdapter`). |

### Application Layer

Application-layer modules provide framework-agnostic domain patterns.

| Module | Package | Purpose |
|---|---|---|
| **Validation** | `pyfly.validation` | Input validation decorators (`@validate_input`, `@validator`) and Pydantic model validation (`validate_model`). |
| **CQRS** | `pyfly.cqrs` | Command/Query Responsibility Segregation: `Command`, `Query`, `CommandHandler`, `QueryHandler`, `Mediator`, and middleware (`LoggingMiddleware`, `MetricsMiddleware`). |
| **EDA** | `pyfly.eda` | Event-Driven Architecture: `EventPublisher` port, `EventEnvelope`, `@event_listener`, `@publish_result`, `InMemoryEventBus`, `ErrorStrategy`. |

### Infrastructure Layer

Infrastructure modules follow the hexagonal pattern: ports in `ports/`, adapters in
`adapters/`.

| Module | Package | Ports | Adapters |
|---|---|---|---|
| **Web** | `pyfly.web` | Mappings (`@get_mapping`, `@post_mapping`, etc.), params (`Body`, `PathVar`, `QueryParam`, `Header`, `Cookie`, `Valid`), `CORSConfig`, `SecurityHeadersConfig`, `WebFilter` protocol, `OncePerRequestFilter`, `@exception_handler`. Config-driven adapter selection (`pyfly.web.adapter`). | Starlette/ASGI (`StarletteWebAdapter`, `ControllerRegistrar`, `create_app`, `WebFilterChainMiddleware`, built-in filters). |
| **Data** | `pyfly.data` | `RepositoryPort`, `SessionPort`, `QueryMethodCompilerPort`. | SQLAlchemy (`Repository`, `Specification`, `FilterUtils`, `@query`, `QueryMethodCompiler`, `RepositoryBeanPostProcessor`), MongoDB (`MongoRepository`, `BaseDocument`, `MongoQueryMethodCompiler`, `MongoRepositoryBeanPostProcessor`). |
| **Messaging** | `pyfly.messaging` | `MessageBrokerPort`, `MessageHandler`, `Message`, `@message_listener`. | Kafka (`KafkaAdapter`), RabbitMQ (`RabbitMQAdapter`), in-memory (`InMemoryMessageBroker`). |
| **Cache** | `pyfly.cache` | `CacheAdapter`, `CacheManager`, `@cacheable`, `@cache_evict`, `@cache_put`. | Redis (`RedisCacheAdapter`), in-memory (`InMemoryCache`). |
| **Client** | `pyfly.client` | `HttpClientPort`, `ServiceClient`, `CircuitBreaker`, `RetryPolicy`, declarative `@http_client` with `@get`, `@post`, `@put`, `@patch`, `@delete`. | HTTPX (`HttpxClientAdapter`), `HttpClientBeanPostProcessor`. |
| **Scheduling** | `pyfly.scheduling` | `TaskExecutorPort`, `CronExpression`, `TaskScheduler`, `@scheduled`, `@async_method`. | AsyncIO (`AsyncIOTaskExecutor`), thread pool (`ThreadPoolTaskExecutor`). |
| **Security** | `pyfly.security` | `SecurityContext`, `PasswordEncoder`, `@secure`. | `JWTService`, `BcryptPasswordEncoder`, `SecurityMiddleware`. |
| **Actuator** | `pyfly.actuator` | `HealthIndicator`, `HealthAggregator`, `HealthResult`, `HealthStatus`, `ActuatorEndpoint` protocol, `ActuatorRegistry`. | Extensible HTTP endpoints (`make_starlette_actuator_routes`), built-in: health, beans, env, info, loggers, metrics. Per-endpoint enable/disable via config. |

### Cross-Cutting Layer

Cross-cutting modules provide capabilities that span all other layers.

| Module | Package | Purpose |
|---|---|---|
| **AOP** | `pyfly.aop` | Aspect-Oriented Programming: `@aspect`, `@before`, `@after`, `@around`, `@after_returning`, `@after_throwing`, pointcut matching (`matches_pointcut`), `AspectBeanPostProcessor`, `JoinPoint`, `AspectRegistry`. |
| **Observability** | `pyfly.observability` | Metrics (`@timed`, `@counted`, `MetricsRegistry`), tracing (`@span`), health checks (`HealthChecker`, `HealthResult`, `HealthStatus`), structured logging (`configure_logging`, `get_logger`). |
| **Resilience** | `pyfly.resilience` | Rate limiting (`@rate_limiter`, `RateLimiter`), bulkhead (`@bulkhead`, `Bulkhead`), timeout (`@time_limiter`), fallback (`@fallback`). |
| **Testing** | `pyfly.testing` | Test utilities (`PyFlyTestCase`, `create_test_container`), event assertions (`assert_event_published`, `assert_no_events_published`). |
| **CLI** | `pyfly.cli` | Project scaffolding and management commands. |

### Layer Diagram

```
+-----------------------------------------------------------------------+
|                         Cross-Cutting Layer                           |
|   aop    observability    resilience    testing    cli                |
+-----------------------------------------------------------------------+
          |                   |                  |
+-----------------------------------------------------------------------+
|                       Infrastructure Layer                            |
|   web    data    messaging    cache    client    scheduling           |
|   security    actuator                                                |
|                                                                       |
|   Each module:  ports/  <--  adapters/                                |
+-----------------------------------------------------------------------+
          |                   |                  |
+-----------------------------------------------------------------------+
|                        Application Layer                              |
|   validation    cqrs    eda                                           |
+-----------------------------------------------------------------------+
          |                   |                  |
+-----------------------------------------------------------------------+
|                        Foundation Layer                               |
|   kernel    core    container    context    config    logging         |
+-----------------------------------------------------------------------+
```

### Module Structure Convention

Every infrastructure module follows this standard layout:

```
pyfly/
  <module>/
    __init__.py          # Public API exports
    ports/
      __init__.py
      outbound.py        # Protocol definitions (ports)
    adapters/
      __init__.py
      memory.py          # In-memory adapter (testing / fallback)
      <vendor>/          # Vendor-specific adapter
        __init__.py
        ...
    decorators.py        # Module-specific decorators
    types.py             # Data types and enums
    *.py                 # Domain logic
```

---

## The Startup Sequence in Detail

The startup sequence is divided across the `PyFlyApplication` constructor, the
`startup()` async method, and the `ApplicationContext.start()` method.

### Phase 1: PyFlyApplication Constructor

When `PyFlyApplication(app_class)` is called:

1. **Read metadata** from the `@pyfly_application`-decorated class: `name`, `version`,
   `scan_packages`, `description`.
2. **Find config file** -- check the explicit `config_path`, then auto-discover by checking
   candidates in order: `pyfly.yaml`, `pyfly.toml`, `config/pyfly.yaml`, `config/pyfly.toml`.
3. **Resolve profiles early** -- call `_resolve_profiles_early()` which reads
   `PYFLY_PROFILES_ACTIVE` env var, then reads `pyfly.profiles.active` from the raw
   base config file (using `yaml.safe_load`). This must happen before full config loading
   so profile overlay files can be merged.
4. **Load configuration** via `Config.from_file()`, which merges:
   - Framework defaults (`pyfly-defaults.yaml` via `importlib.resources`)
   - Base config file
   - Profile overlay files (for each active profile)
5. **Configure logging** -- create `StructlogAdapter`, configure from the logging section
   of the config.
6. **Create ApplicationContext** -- wraps a new `Container`, `Environment`, and
   `ApplicationEventBus`. The `Config` object is registered as a singleton bean so it can
   be injected into any component.
7. **Scan packages** -- for each package in `scan_packages`, call `scan_package()` which
   recursively discovers and registers stereotype-decorated classes. Logs the package name
   and bean count for each scan.

### Phase 2: startup()

When `await app.startup()` is called:

1. **Render and print banner** -- create `BannerPrinter.from_config()`, render the banner
   text (ASCII art, minimal, or off), print to stdout, flush.
2. **Log startup info** -- `"Starting {app} v{version}"`.
3. **Log profiles** -- `"Active profiles: [...]"` or `"No active profiles set, falling back to default"`.
4. **Call `await ApplicationContext.start()`** -- the core initialization (Phase 3).
5. **Record startup time** -- `time.perf_counter()` delta.
6. **Log completion** -- `"Started {app} in {time}s ({count} beans initialized)"`.

### Phase 3: ApplicationContext.start()

This is where the bulk of the DI and lifecycle work happens. The steps are:

1. **Filter by profile** -- `_filter_by_profile()` removes registrations whose
   `__pyfly_profile__` expression does not match the `Environment.active_profiles`.
   Uses `Environment.accepts_profiles()` which supports negation and comma-separated OR.

2. **Evaluate conditions (pass 1)** -- `ConditionEvaluator.should_include(cls, bean_pass=False)`
   removes beans that fail non-bean-dependent conditions:
   - `@conditional_on_property` -- config key must exist (and optionally match a value).
   - `@conditional_on_class` -- Python module must be importable.
   - Stereotype `condition` callable -- must return `True`.

3. **Process user `@configuration` classes** -- `_process_configurations(auto=False)`:
   - Find all `@configuration`-stereotyped classes that are NOT `@auto_configuration`.
   - Resolve the configuration class itself.
   - Find `@bean`-decorated methods.
   - Read the return type hint to determine the bean type.
   - Call each method (injecting parameters from the container).
   - Register the produced bean by its return type.

4. **Evaluate conditions (pass 2)** -- `ConditionEvaluator.should_include(cls, bean_pass=True)`
   removes beans that fail bean-dependent conditions:
   - `@conditional_on_bean` -- another bean of the specified type must exist.
   - `@conditional_on_missing_bean` -- no bean of the specified type must exist.
   This runs after user `@configuration` processing so user-provided beans are visible.

5. **Process `@auto_configuration` classes** -- `_process_configurations(auto=True)`:
   same as step 3 but only for classes with `__pyfly_auto_configuration__ = True`.

6. **Run `AutoConfigurationEngine`** -- imperative auto-configuration that detects
   available providers and registers adapter beans for cache, messaging, client, and
   data subsystems. Skips any subsystem where the user has already registered a bean.

7. **Eagerly resolve all singletons** -- sorted by `@order` value (lower = higher
   priority = resolved first). For each singleton registration with no cached instance,
   call `container.resolve()` (which triggers constructor injection recursively).
   Resolution failures are silently suppressed via `contextlib.suppress(KeyError)`.

8. **Run post-processors and lifecycle hooks** -- for each resolved bean instance,
   in registration order:
   - All `BeanPostProcessor.before_init()` methods (sorted by `@order` of the post-processor).
   - All `@post_construct` methods on the bean (async-aware: if the method returns an
     awaitable, it is `await`ed).
   - All `BeanPostProcessor.after_init()` methods (sorted by `@order` of the post-processor).
   Post-processors can return replacement beans (enabling proxy patterns like AOP).

9. **Publish lifecycle events**:
   - `ContextRefreshedEvent` -- signals that the context is fully initialized.
   - `ApplicationReadyEvent` -- signals that the application is ready to serve requests.

### Complete Startup Flow Diagram

```
PyFlyApplication.__init__(app_class)
    |
    +-- Read @pyfly_application metadata
    +-- Find config file (auto-discover or explicit)
    +-- Resolve profiles early (env var or config file)
    +-- Config.from_file() (merge defaults + base + profiles)
    +-- Configure logging (StructlogAdapter)
    +-- Create ApplicationContext (Container + Environment + EventBus)
    +-- Register Config as singleton bean
    +-- Scan packages -> register stereotype beans
    |
await app.startup()
    |
    +-- Render & print banner (TEXT / MINIMAL / OFF)
    +-- Log "Starting {app} v{version}"
    +-- Log active profiles
    |
    +-- await ApplicationContext.start()
    |       |
    |       +-- 1. Filter beans by profile expression
    |       +-- 2. Evaluate conditions (pass 1: on_property, on_class)
    |       +-- 3. Process user @configuration classes + @bean methods
    |       +-- 4. Evaluate conditions (pass 2: on_bean, on_missing_bean)
    |       +-- 5. Process @auto_configuration classes + @bean methods
    |       +-- 6. Run AutoConfigurationEngine (provider detection)
    |       +-- 6a. Start infrastructure adapters (fail-fast)
    |       |       +-- For each adapter: await adapter.start()
    |       |       +-- On failure: BeanCreationException
    |       +-- 7. Eagerly resolve singletons (sorted by @order)
    |       +-- 8. For each bean:
    |       |       +-- BeanPostProcessor.before_init()
    |       |       +-- @post_construct methods
    |       |       +-- BeanPostProcessor.after_init()
    |       +-- 9. Publish ContextRefreshedEvent
    |       +-- 10. Publish ApplicationReadyEvent
    |
    +-- Record startup time
    +-- Log "Started {app} in {time}s ({count} beans)"
```

### Shutdown Sequence

```
await app.shutdown()
    |
    +-- Log "Shutting down {app}"
    +-- await ApplicationContext.stop()
            |
            +-- Stop infrastructure adapters (reverse order)
            |       +-- For each adapter: await adapter.stop()
            +-- Call @pre_destroy on all beans (reverse order)
            +-- Publish ContextClosedEvent
```

---

## Dependency Injection Architecture

### Container vs ApplicationContext

PyFly's DI system has two layers, each with a distinct responsibility:

| Component | Role | When to Use |
|---|---|---|
| `Container` | Low-level DI engine. Stores `Registration` objects, resolves by type hints, handles scopes, `@primary`, and `Qualifier`. No lifecycle awareness. | Standalone tests, framework extensions, custom resolution logic. |
| `ApplicationContext` | High-level orchestrator. Wraps the Container and adds `@bean` factory methods, lifecycle hooks, post-processors, profile filtering, condition evaluation, auto-configuration, and events. | Always use in application code. |

The `ApplicationContext` exposes the underlying container via its `container` property
as an escape hatch for advanced use cases.

### Registration and Resolution

Bean registration happens through multiple channels:

1. **Component scanning** -- `scan_package()` discovers stereotype-decorated classes and
   calls `container.register()` for each.
2. **Manual registration** -- `container.register(cls)` or `context.register_bean(cls)`.
3. **@bean factory methods** -- methods inside `@configuration` classes, processed by
   `_process_configurations()`.
4. **Auto-configuration** -- `AutoConfigurationEngine` registers adapter beans directly
   into the container.

Resolution follows these rules (in `Container.resolve()`):

1. **Direct registration** -- if the requested type has a `Registration`, use it.
2. **Interface binding** -- check `_bindings` for the type. If exactly one implementation
   is bound, resolve it.
3. **@primary disambiguation** -- if multiple implementations are bound, select the one
   with `__pyfly_primary__ = True`.
4. **Qualifier** -- when a constructor parameter uses `Annotated[T, Qualifier("name")]`,
   resolution bypasses type-based lookup and uses `resolve_by_name()` directly.

Constructor dependencies are resolved recursively. The container inspects
`typing.get_type_hints(init, include_extras=True)` to discover parameter types, including
`Annotated` metadata.

### Stereotype System

All stereotypes (`@component`, `@service`, `@repository`, `@controller`,
`@rest_controller`, `@configuration`) are generated by the `_make_stereotype()` factory
in `pyfly.container.stereotypes`. They are functionally identical at the container level.
The differences are:

- **Semantic**: the `__pyfly_stereotype__` string communicates architectural intent.
- **Processing**: `"configuration"` triggers `@bean` method scanning in
  `ApplicationContext._process_configurations()`.
- **Discovery**: `"rest_controller"` is used by the web layer to find controllers.
- **Extensibility**: future features (e.g., repository exception translation) can key
  off the stereotype label.

---

## Auto-Configuration

PyFly provides two auto-configuration mechanisms that work together.

### Declarative Auto-Configuration

The `@auto_configuration` decorator (from `pyfly.context.conditions`) marks a
`@configuration` class for deferred processing. Combined with `@conditional_on_*`
decorators, it provides "default with override" semantics:

```python
@auto_configuration
@conditional_on_missing_bean(CacheAdapter)
@conditional_on_class("redis.asyncio")
class RedisCacheAutoConfig:
    @bean
    def cache(self) -> CacheAdapter:
        return RedisCacheAdapter(...)
```

This bean is only created if (1) no user-provided `CacheAdapter` exists and (2) the
`redis` library is installed.

Auto-configuration classes:
- Receive an implicit `@order(1000)` (lower priority than user beans at default 0).
- Are processed after user `@configuration` classes.
- Have `__pyfly_auto_configuration__ = True`, `__pyfly_injectable__ = True`, and
  `__pyfly_stereotype__ = "configuration"` set by the decorator.

### Imperative Auto-Configuration

The `AutoConfigurationEngine` (from `pyfly.config.auto`) runs after all declarative
configuration. It reads config properties to determine which subsystems are enabled,
detects available providers, and registers appropriate adapter beans.

For each subsystem, the engine:

1. Checks if a bean for the port type is already registered (user override). If so, skip.
2. Checks if the subsystem is enabled in config (e.g., `pyfly.cache.enabled`).
3. Reads the configured provider (e.g., `pyfly.cache.provider`).
4. If provider is `"auto"`, calls the detection method (e.g., `detect_cache_provider()`).
5. Imports and instantiates the appropriate adapter.
6. Registers it as a singleton bean.

The engine tracks results in a `results` dict mapping subsystem names to provider names.

### Provider Detection

The `AutoConfiguration` class provides static detection methods that check library
availability via `importlib.import_module()`:

| Subsystem | Method | Detection Order | Returns |
|---|---|---|---|
| Web | `detect_web_adapter()` | `starlette` | `"starlette"` or `"none"` |
| Cache | `detect_cache_provider()` | `redis.asyncio` | `"redis"` or `"memory"` |
| Messaging | `detect_eda_provider()` | `aiokafka`, then `aio_pika` | `"kafka"`, `"rabbitmq"`, or `"memory"` |
| HTTP Client | `detect_client_provider()` | `httpx` | `"httpx"` or `"none"` |
| Data Relational | `detect_relational_provider()` | `sqlalchemy` | `"sqlalchemy"` or `"none"` |
| Data Document | `detect_document_provider()` | `motor`, then `beanie` | `"mongodb"` or `"none"` |

---

## Framework-Agnostic Design

Each infrastructure module separates framework-agnostic types from adapter-specific
implementations. This separation ensures business code never imports technology-specific
libraries directly.

### Web Module

```
pyfly.web/
    mappings.py          # @get_mapping, @post_mapping, @put_mapping,
    |                    # @patch_mapping, @delete_mapping, @request_mapping
    params.py            # Body, PathVar, QueryParam, Header, Cookie, Valid
    filters.py           # OncePerRequestFilter base class
    cors.py              # CORSConfig
    security_headers.py  # SecurityHeadersConfig
    exception_handler.py # @exception_handler
    ports/
        outbound.py      # WebServerPort protocol
        filter.py        # WebFilter protocol, CallNext type alias
    adapters/
        starlette/       # Starlette/ASGI implementation
            adapter.py           # StarletteWebAdapter (WebServerPort impl)
            app.py               # create_app() factory
            controller.py        # ControllerRegistrar
            resolver.py          # ParameterResolver (with Valid[T] support)
            filter_chain.py      # WebFilterChainMiddleware
            filters/             # Built-in filter implementations
                transaction_id_filter.py
                request_logging_filter.py
                security_headers_filter.py
                security_filter.py
```

Framework-agnostic decorators (`@get_mapping`, `@post_mapping`), parameter types
(`Body`, `QueryParam`, `Valid`), and the `WebFilter` protocol work with any web
framework. The Starlette adapter is the default; config-driven selection
(`pyfly.web.adapter: auto|starlette`) allows future adapters.

### Data Module

```
pyfly/data/                     # Data Commons
├── page.py                     # Page[T]
├── pageable.py                 # Pageable, Sort, Order
├── mapper.py                   # Mapper
├── query_parser.py             # QueryMethodParser
├── ports/                      # Shared ports
│   ├── outbound.py             # RepositoryPort, SessionPort
│   └── compiler.py             # QueryMethodCompilerPort
├── relational/                 # Relational namespace
│   └── sqlalchemy/             # SQLAlchemy adapter
│       ├── entity.py           # Base, BaseEntity
│       ├── repository.py       # Repository[T, ID]
│       ├── specification.py    # Specification
│       ├── filter.py           # FilterOperator, FilterUtils
│       ├── query.py            # @query, QueryExecutor
│       ├── query_compiler.py   # QueryMethodCompiler
│       ├── post_processor.py   # RepositoryBeanPostProcessor
│       └── transactional.py    # reactive_transactional
└── document/                   # Document namespace
    └── mongodb/                # MongoDB adapter
        ├── document.py         # BaseDocument
        ├── repository.py       # MongoRepository[T, ID]
        ├── query_compiler.py   # MongoQueryMethodCompiler
        ├── post_processor.py   # MongoRepositoryBeanPostProcessor
        ├── transactional.py    # mongo_transactional
        └── initializer.py      # initialize_beanie()
```

### Messaging Module

```
pyfly.messaging/
    types.py           # Message dataclass
    decorators.py      # @message_listener
    ports/
        outbound.py    # MessageBrokerPort, MessageHandler
    adapters/
        memory.py      # InMemoryMessageBroker (testing / fallback)
        kafka.py       # KafkaAdapter (aiokafka)
        rabbitmq.py    # RabbitMQAdapter (aio_pika)
```

### Cache Module

```
pyfly.cache/
    decorators.py     # @cacheable, @cache_evict, @cache_put, @cache
    manager.py        # CacheManager
    ports/
        outbound.py   # CacheAdapter
    adapters/
        memory.py     # InMemoryCache
        redis.py      # RedisCacheAdapter (redis.asyncio)
```

### Scheduling Module

```
pyfly.scheduling/
    decorators.py       # @scheduled, @async_method
    cron.py             # CronExpression parser
    task_scheduler.py   # TaskScheduler
    ports/
        outbound.py     # TaskExecutorPort
    adapters/
        asyncio_executor.py   # AsyncIOTaskExecutor
        thread_executor.py    # ThreadPoolTaskExecutor
```

---

## Configuration Architecture

Configuration follows a layered loading strategy with four levels:

```
+---------------------------------------------------+
| 4. Environment Variables  (read-time priority)    |
+---------------------------------------------------+
| 3. Profile Overlays       (pyfly-{profile}.yaml)  |
+---------------------------------------------------+
| 2. User Config File       (pyfly.yaml / .toml)    |
+---------------------------------------------------+
| 1. Framework Defaults     (pyfly-defaults.yaml)   |
+---------------------------------------------------+
```

Key architectural decisions:

- **Deep merge** -- nested dictionaries are merged recursively (`Config._deep_merge()`),
  not replaced wholesale. This lets profile overlays specify only the keys that change.
- **Read-time env var resolution** -- environment variables are not baked into the config
  dict at load time. They are checked on every `Config.get()` call, ensuring they always
  win. The mapping strips the `pyfly.` prefix, replaces dots and hyphens with underscores,
  uppercases, and prefixes with `PYFLY_`.
- **Typed binding** -- `@config_properties` dataclasses provide compile-time type
  safety and IDE support. The `Config.bind()` method handles type coercion for `int`,
  `float`, and `bool` fields.
- **Early profile resolution** -- profiles must be resolved before `Config.from_file()`
  runs, because the method needs to know which overlay files to merge. This is handled
  by `PyFlyApplication._resolve_profiles_early()`, which reads the env var first, then
  parses the raw YAML file to extract the `pyfly.profiles.active` value.
- **Dual format support** -- YAML (via `PyYAML`) and TOML (via `tomllib`) are both
  supported. The format is determined by the file extension.

---

## Event-Driven Design

PyFly supports two separate event systems for different concerns.

### Application Events

Application events are lifecycle notifications published by the `ApplicationContext`.
They use `ApplicationEventBus` (in-process, ordered dispatch with async listeners).

| Event | When Published |
|---|---|
| `ContextRefreshedEvent` | After all beans are initialized and post-processed. |
| `ApplicationReadyEvent` | Immediately after `ContextRefreshedEvent`. |
| `ContextClosedEvent` | After all `@pre_destroy` methods during shutdown. |

All events inherit from `ApplicationEvent`. Listeners are invoked in `@order` order of
their owning class.

Application events are for framework-level lifecycle coordination (e.g., "start accepting
HTTP requests after all beans are ready").

### Domain Events (EDA)

The `pyfly.eda` module provides a separate event system for domain-level events:

- `EventPublisher` port -- abstract interface for publishing domain events.
- `EventEnvelope` -- wraps events with metadata (timestamp, correlation ID, etc.).
- `@event_listener` -- decorator for domain event handlers.
- `@event_publisher` -- decorator for classes that publish events.
- `@publish_result` -- decorator to automatically publish a method's return value.
- `InMemoryEventBus` -- default in-process adapter.
- `ErrorStrategy` -- configurable error handling for event processing.

Domain events flow through the `EventPublisher` port and can be routed to external
systems (Kafka, RabbitMQ) via adapter binding.

The two systems are intentionally separate: application events are internal lifecycle
signals; domain events are part of your business logic.

---

## Cross-Cutting Concerns

### Aspect-Oriented Programming

The `pyfly.aop` module provides Spring-style AOP:

- `@aspect` -- marks a class as an aspect container.
- `@before`, `@after`, `@around`, `@after_returning`, `@after_throwing` -- advice
  decorators with pointcut expressions.
- `AspectBeanPostProcessor` -- a `BeanPostProcessor` that weaves aspects into target
  beans during `after_init()`.
- `JoinPoint` -- provides context about the intercepted method call.
- `AspectRegistry` / `AdviceBinding` -- manages the mapping of pointcuts to advice.

AOP is implemented through proxy wrapping in `BeanPostProcessor.after_init()`, which
means it works seamlessly with the DI lifecycle. The `weave_bean()` function performs
the actual weaving.

### Observability

The `pyfly.observability` module provides:

- **Metrics**: `@timed` and `@counted` decorators for automatic metric collection, `MetricsRegistry` for programmatic metric access.
- **Tracing**: `@span` decorator for distributed tracing.
- **Health checks**: `HealthChecker` with `HealthResult` and `HealthStatus`.
- **Logging**: `configure_logging()` and `get_logger()` for structured logging.

The `pyfly.actuator` module exposes health and info endpoints for production monitoring
via `make_actuator_routes()`.

### Resilience

The `pyfly.resilience` module provides resilience patterns as decorators:

- `@rate_limiter` / `RateLimiter` -- limits call frequency.
- `@bulkhead` / `Bulkhead` -- limits concurrent executions.
- `@time_limiter` -- enforces execution timeouts.
- `@fallback` -- provides fallback values on failure.

The `pyfly.client` module adds `CircuitBreaker` (with `CircuitState`) and `RetryPolicy`
for HTTP client resilience.

### Security

The `pyfly.security` module provides:

- `SecurityContext` -- holds the current user/principal.
- `@secure` -- method-level authorization decorator.
- `JWTService` -- JWT token creation and validation.
- `SecurityMiddleware` -- HTTP request authentication middleware.
- `PasswordEncoder` / `BcryptPasswordEncoder` -- password hashing.

### Validation

The `pyfly.validation` module integrates with Pydantic:

- `@validate_input` -- validates method arguments against Pydantic models.
- `@validator` -- custom validation decorators.
- `validate_model()` -- programmatic model validation.
- `Valid[T]` -- web parameter annotation that triggers explicit validation with
  structured 422 error responses. Works standalone (`Valid[CreateDTO]` = body
  validation) or wrapping any binding type (`Valid[QueryParam[int]]`).

---

## Design Decisions and Trade-Offs

### Injection Strategy

PyFly supports two injection styles, mirroring Spring Boot:

1. **Constructor injection** (preferred) — dependencies declared as `__init__` type hints.
   Dependencies are explicit, immutable, and visible in the class signature.
2. **Field injection** via `Autowired()` — dependencies declared as class attributes.
   Useful when constructor parameter lists grow large or for optional collaborators.

Additional injection features:
- **`Optional[T]`** — resolves to `None` when the dependency is not registered.
- **`list[T]`** — collects all implementations bound to an interface.
- **Circular dependency detection** — the container tracks types currently being
  resolved and raises `CircularDependencyError` with a clear chain message instead
  of infinite recursion.

**Recommendation:** prefer constructor injection for mandatory dependencies.
Use `Autowired()` for optional or supplemental dependencies where it improves
readability. Deeply nested dependency graphs with many constructor parameters are
a signal to refactor into smaller components.

### Why Async-First?

All lifecycle methods (`startup()`, `shutdown()`, `@post_construct`, `@pre_destroy`),
event handlers, and I/O operations are async.

**Rationale:**
- Modern Python services are I/O-bound (HTTP, databases, message brokers). `async/await`
  provides efficient concurrency without threads.
- ASGI web servers (Uvicorn, Hypercorn) require async handlers.
- Database drivers (asyncpg, aiosqlite) and message broker clients (aiokafka, aio_pika)
  are async-native.

**Trade-off:** CPU-bound work must be offloaded to thread pools or process pools. The
`@async_method` decorator and `ThreadPoolTaskExecutor` provide escape hatches.

### Why Protocols over ABCs?

Ports use `typing.Protocol` (structural typing) rather than `abc.ABC` (nominal typing).

**Rationale:**
- Protocol classes define contracts without requiring inheritance. Any class that
  implements the right methods satisfies the protocol, even without explicitly subclassing.
- This supports duck typing, which is idiomatic Python.
- It reduces coupling: adapter classes do not need to know about or import the port
  definitions (though they usually do for clarity).
- The `BeanPostProcessor` protocol uses `@runtime_checkable` so it can be checked with
  `isinstance()` when needed.

**Trade-off:** Protocol violations are caught at type-check time (mypy/pyright) rather
than at class definition time. This means errors may surface later if type checking is
not enforced.

### Why Two DI Layers (Container + ApplicationContext)?

**Rationale:**
- The `Container` is a focused, simple DI engine that can be used standalone (especially
  in tests via `create_test_container()`).
- The `ApplicationContext` adds lifecycle concerns (events, post-processors, conditions,
  auto-configuration) that would complicate the Container's API.
- This separation follows the Single Responsibility Principle and makes each layer
  independently testable.

**Trade-off:** users must understand which layer to use. The guideline is simple:
use `ApplicationContext` in application code, use `Container` directly only in tests
or framework extensions.

### Why Declarative + Imperative Auto-Configuration?

**Rationale:**
- Declarative auto-configuration (`@auto_configuration` with `@conditional_on_*`)
  is flexible and extensible -- users and library authors can create custom
  auto-configuration classes.
- Imperative auto-configuration (`AutoConfigurationEngine`) handles the common case
  of detecting installed libraries and wiring adapters, without requiring users to
  understand the condition system.
- The two approaches complement each other: declarative for customization, imperative
  for convention.

### Why Deep Merge Instead of Override?

**Rationale:**
- Deep merge lets profile overlays specify only changed keys. Without it, you would
  need to duplicate the entire config tree in every profile file.
- It matches the mental model of "this profile changes these specific settings."

**Trade-off:** you cannot "unset" a key by omitting it in an overlay. To effectively
remove a value, you must explicitly set it to `null`/`""` in the overlay file.

### Key Design Patterns Used

| Pattern | Module | Description |
|---|---|---|
| **Repository** | `pyfly.data` | Abstract data access behind ports. |
| **Specification** | `pyfly.data` | Composable query predicates. |
| **Circuit Breaker** | `pyfly.client` | Prevent cascading failures. |
| **Mediator** | `pyfly.cqrs` | Route commands/queries to handlers. |
| **Chain of Responsibility** | `pyfly.web` | Exception converter chain. |
| **Observer** | `pyfly.context`, `pyfly.eda` | Application and domain events. |
| **Decorator** | `pyfly.aop` | Aspect-oriented cross-cutting concerns via proxies. |
| **Factory** | `pyfly.container` | Bean factories via `@configuration` / `@bean`. |
| **Builder** | `pyfly.client` | Fluent `ServiceClient.rest()` builder. |
| **Strategy** | `pyfly.resilience` | Pluggable resilience policies. |
| **Template Method** | `pyfly.context` | `ApplicationContext.start()` orchestration. |
