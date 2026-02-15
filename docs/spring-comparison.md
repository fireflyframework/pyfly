# Spring Boot Comparison Guide

**A comprehensive mapping from Spring Boot to PyFly for Java developers.**

If you're coming from the Java/Spring Boot ecosystem, this guide shows you how every concept you know translates into PyFly. Each section explains not just *what* maps to *what*, but *why* PyFly chose its approach and how the Python-native design differs from the Java original.

---

## Table of Contents

- [Application Entry Point](#application-entry-point)
- [Dependency Injection](#dependency-injection)
- [Bean Stereotypes](#bean-stereotypes)
- [Bean Configuration](#bean-configuration)
- [Conditional Beans](#conditional-beans)
- [Lifecycle Hooks](#lifecycle-hooks)
- [Configuration Properties](#configuration-properties)
- [Profiles](#profiles)
- [Web Controllers](#web-controllers)
- [Request Parameters](#request-parameters)
- [Exception Handling](#exception-handling)
- [Data Access](#data-access)
- [Caching](#caching)
- [Scheduling](#scheduling)
- [Aspect-Oriented Programming](#aspect-oriented-programming)
- [Resilience Patterns](#resilience-patterns)
- [Observability](#observability)
- [Messaging](#messaging)
- [Quick Reference Table](#quick-reference-table)

---

## Application Entry Point

### Spring Boot

```java
@SpringBootApplication
public class MyApplication {
    public static void main(String[] args) {
        SpringApplication.run(MyApplication.class, args);
    }
}
```

`@SpringBootApplication` is a convenience annotation that combines `@Configuration`, `@EnableAutoConfiguration`, and `@ComponentScan`.

### PyFly

```python
from pyfly.core import pyfly_application, PyFlyApplication

@pyfly_application(
    name="my-service",
    version="0.1.0",
    scan_packages=["my_service"],
)
class Application:
    pass

# Start the application
app = PyFlyApplication(Application)
await app.startup()
```

**Key difference:** In Spring, component scanning is classpath-based and implicit. In PyFly, `scan_packages` explicitly lists which Python packages to scan for decorated classes. This is deliberate — Python's import system doesn't have Java's classpath scanning, so explicit package listing is more predictable and avoids accidental imports from third-party libraries.

**Configuration:** Spring uses `application.yml` or `application.properties`. PyFly uses `pyfly.yaml` with the same hierarchical structure. See [Configuration Guide](guides/configuration.md).

---

## Dependency Injection

### Spring Boot

```java
@Service
public class OrderService {
    private final OrderRepository repo;
    private final EventPublisher events;

    @Autowired  // Optional in modern Spring with single constructor
    public OrderService(OrderRepository repo, EventPublisher events) {
        this.repo = repo;
        this.events = events;
    }
}
```

### PyFly — Constructor Injection (Preferred)

```python
@service
class OrderService:
    def __init__(self, repo: OrderRepository, events: EventPublisher) -> None:
        self._repo = repo
        self._events = events
```

### PyFly — Field Injection with `Autowired()`

```python
from pyfly.container import Autowired

@service
class OrderService:
    repo: OrderRepository = Autowired()
    events: EventPublisher = Autowired()
    metrics: MetricsCollector = Autowired(required=False)  # optional
```

**How it works:** PyFly supports both constructor injection and field injection, matching Spring Boot's capabilities. Constructor injection is the recommended default — it makes dependencies explicit and enables immutability. Field injection via `Autowired()` is available for cases where it improves readability or for optional dependencies.

The container inspects `__init__` type hints for constructor injection and class annotations for `Autowired()` sentinels. After constructing the instance, it injects any `Autowired` fields via `setattr`.

### Optional and Collection Injection

```python
from typing import Optional

@service
class OrderService:
    def __init__(
        self,
        repo: OrderRepository,
        cache: Optional[CacheAdapter] = None,    # None if not registered
        validators: list[Validator] = [],          # all implementations
    ) -> None:
        self._repo = repo
        self._cache = cache
        self._validators = validators
```

`Optional[T]` resolves to `None` when no bean of type `T` is registered. `list[T]` collects all implementations bound to `T` — equivalent to Spring's `List<T>` injection.

### Qualifier / Named Beans

**Spring:**
```java
@Autowired
public OrderService(@Qualifier("postgresRepo") OrderRepository repo) { }
```

**PyFly:**
```python
from typing import Annotated
from pyfly.container import Qualifier

@service
class OrderService:
    def __init__(self, repo: Annotated[OrderRepository, Qualifier("postgres_repo")]) -> None:
        self._repo = repo
```

PyFly uses Python's `Annotated` type hint with `Qualifier` metadata instead of a separate annotation. This keeps the type system clean — the base type is still `OrderRepository` for type checking, while `Qualifier` provides the additional lookup hint.

### Primary Bean

**Spring:**
```java
@Primary
@Repository
public class PostgresOrderRepo implements OrderRepository { }
```

**PyFly:**
```python
@primary
@repository
class PostgresOrderRepo:
    """This implementation is used when multiple OrderRepository beans exist."""
    pass
```

When multiple beans satisfy the same type, `@primary` marks the default.

---

## Bean Stereotypes

Spring and PyFly share the same stereotype hierarchy, but the semantics are slightly different:

| Spring | PyFly | Scope | Purpose |
|--------|-------|-------|---------|
| `@Component` | `@component` | Singleton | Generic managed bean |
| `@Service` | `@service` | Singleton | Business logic |
| `@Repository` | `@repository` | Singleton | Data access |
| `@Controller` | `@rest_controller` | Singleton | HTTP endpoints |
| `@Configuration` | `@configuration` | Singleton | Bean factory class |

**Why PyFly uses `@rest_controller` instead of `@controller`:** In Spring, `@Controller` renders views and `@RestController` returns JSON. Since PyFly is API-first and doesn't have a templating engine, `@rest_controller` is the standard stereotype. It automatically serializes return values to JSON.

### Stereotype Behavior

All stereotypes in both frameworks:
- Mark the class as a **managed bean** (created and owned by the container)
- Default to **singleton scope** (one instance per application)
- Enable **component scanning** (auto-discovered at startup)
- Support **constructor injection** (dependencies resolved automatically)

---

## Bean Configuration

### Spring Boot

```java
@Configuration
public class DatabaseConfig {
    @Bean
    public DataSource dataSource() {
        return new HikariDataSource(hikariConfig());
    }

    @Bean
    @ConditionalOnProperty(name = "cache.enabled", havingValue = "true")
    public CacheManager cacheManager() {
        return new RedisCacheManager();
    }
}
```

### PyFly

```python
@configuration
class DatabaseConfig:
    @bean
    def data_source(self) -> DataSource:
        return HikariDataSource(self._hikari_config())

    @bean
    @conditional_on_property("cache.enabled", having_value="true")
    def cache_manager(self) -> CacheManager:
        return RedisCacheManager()
```

**Key difference:** Spring's `@Bean` methods are processed by CGLIB proxying to ensure singleton behavior — calling `dataSource()` twice returns the same instance. PyFly doesn't need this because `@bean` methods are only called once during container initialization; the container manages the singleton lifecycle directly.

**Return type hint:** PyFly uses the return type annotation (`-> DataSource`) to determine what type this bean satisfies. This is equivalent to Spring inferring the bean type from the method return type.

---

## Conditional Beans

Both frameworks support conditional bean registration based on runtime conditions:

| Spring | PyFly | Purpose |
|--------|-------|---------|
| `@ConditionalOnProperty` | `@conditional_on_property` | Register only if config key has specific value |
| `@ConditionalOnClass` | `@conditional_on_class` | Register only if a Python module is importable |
| `@ConditionalOnMissingBean` | `@conditional_on_missing_bean` | Register only if no bean of that type exists |
| `@ConditionalOnBean` | `@conditional_on_bean` | Register only if a bean of that type exists |

### Example: Auto-Configuration

```python
@configuration
class CacheAutoConfiguration:
    @bean
    @conditional_on_class("redis")
    def redis_cache(self) -> CacheAdapter:
        return RedisCacheAdapter()

    @bean
    @conditional_on_missing_bean(CacheAdapter)
    def in_memory_cache(self) -> CacheAdapter:
        return InMemoryCache()
```

This mirrors Spring Boot's auto-configuration pattern exactly: if Redis is installed, use it; otherwise, fall back to an in-memory implementation. Your application code depends on `CacheAdapter` (the port) and never knows which implementation is active.

---

## Lifecycle Hooks

### Spring Boot

```java
@Component
public class DataLoader {
    @PostConstruct
    public void init() {
        // Called after dependency injection
    }

    @PreDestroy
    public void cleanup() {
        // Called during shutdown
    }
}
```

### PyFly

```python
@component
class DataLoader:
    @post_construct
    async def init(self) -> None:
        # Called after dependency injection
        await self._load_initial_data()

    @pre_destroy
    async def cleanup(self) -> None:
        # Called during graceful shutdown
        await self._flush_buffers()
```

**Key difference:** PyFly lifecycle hooks are `async` — they can perform I/O operations like loading data from a database or flushing to a message broker. Spring's `@PostConstruct` is synchronous by design.

**Ordering:** Use `@order(N)` to control lifecycle hook execution order across beans, just like Spring's `@Order`.

---

## Configuration Properties

### Spring Boot

```java
@ConfigurationProperties(prefix = "app.datasource")
public class DataSourceProperties {
    private String url;
    private int poolSize = 10;
    // getters, setters
}
```

```yaml
app:
  datasource:
    url: jdbc:postgresql://localhost/mydb
    pool-size: 20
```

### PyFly

```python
from dataclasses import dataclass
from pyfly.core import config_properties

@config_properties(prefix="pyfly.data")
@dataclass
class DataSourceProperties:
    url: str = "sqlite+aiosqlite:///app.db"
    pool_size: int = 10
```

```yaml
pyfly:
  data:
    url: postgresql+asyncpg://localhost/mydb
    pool_size: 20
```

**Key difference:** Spring uses Java beans with getters/setters. PyFly uses Pydantic `BaseModel` classes, which gives you:
- **Automatic validation** — Invalid config values are caught at startup with clear error messages
- **Type coercion** — String environment variables are automatically converted to the right type
- **Immutability** — Config objects are frozen after creation (Pydantic `frozen=True`)
- **Default values** — Python default arguments are cleaner than Java's field initialization

---

## Profiles

### Spring Boot

```yaml
# application-dev.yml
spring:
  datasource:
    url: jdbc:h2:mem:testdb

# application-prod.yml
spring:
  datasource:
    url: jdbc:postgresql://prod-db/mydb
```

Activated via: `spring.profiles.active=dev`

### PyFly

```yaml
# pyfly-dev.yaml
pyfly:
  data:
    url: sqlite+aiosqlite:///dev.db
  logging:
    level:
      root: DEBUG

# pyfly-prod.yaml
pyfly:
  data:
    url: postgresql+asyncpg://prod-db/mydb
  logging:
    level:
      root: WARNING
```

Activated via: `PYFLY_PROFILES_ACTIVE=dev` environment variable, or in `pyfly.yaml`:

```yaml
pyfly:
  profiles:
    active: dev
```

**Configuration layering** (lowest to highest priority):
1. `pyfly-defaults.yaml` — Framework built-in defaults
2. `pyfly.yaml` — Your application defaults
3. `pyfly-{profile}.yaml` — Profile-specific overrides
4. Environment variables — Runtime overrides (highest priority)

This is identical to Spring Boot's property source ordering.

---

## Web Controllers

### Spring Boot

```java
@RestController
@RequestMapping("/api/orders")
public class OrderController {
    private final OrderService service;

    public OrderController(OrderService service) {
        this.service = service;
    }

    @GetMapping
    public List<Order> listOrders() {
        return service.findAll();
    }

    @GetMapping("/{id}")
    public Order getOrder(@PathVariable Long id) {
        return service.findById(id);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public Order createOrder(@RequestBody CreateOrderRequest request) {
        return service.create(request);
    }
}
```

### PyFly

```python
@rest_controller
@request_mapping("/api/orders")
class OrderController:
    def __init__(self, service: OrderService) -> None:
        self._service = service

    @get_mapping("/")
    async def list_orders(self) -> list[dict]:
        return await self._service.find_all()

    @get_mapping("/{id}")
    async def get_order(self, id: int) -> dict:
        return await self._service.find_by_id(id)

    @post_mapping("/", status_code=201)
    async def create_order(self, request: Body[CreateOrderRequest]) -> dict:
        return await self._service.create(request)
```

**Key differences:**
- **Async handlers:** All PyFly handlers are `async` — they run on the asyncio event loop, not a thread pool
- **Path parameters:** In PyFly, path parameters like `{id}` are automatically resolved from method parameter names and type-converted. No `@PathVariable` annotation needed — just matching parameter names
- **Request body:** `Body[T]` is a type alias that tells PyFly to deserialize the request body into a Pydantic model. Spring's `@RequestBody` is an annotation on the parameter
- **Response:** PyFly automatically serializes the return value to JSON. Return `dict`, Pydantic models, or dataclasses

### HTTP Method Mappings

| Spring | PyFly |
|--------|-------|
| `@GetMapping("/path")` | `@get_mapping("/path")` |
| `@PostMapping("/path")` | `@post_mapping("/path")` |
| `@PutMapping("/path")` | `@put_mapping("/path")` |
| `@DeleteMapping("/path")` | `@delete_mapping("/path")` |
| `@PatchMapping("/path")` | `@patch_mapping("/path")` |

---

## Request Parameters

| Spring | PyFly | Description |
|--------|-------|-------------|
| `@PathVariable Long id` | `id: int` | URL path parameter (matched by name) |
| `@RequestParam String name` | `name: QueryParam[str]` | Query string parameter |
| `@RequestBody Order order` | `order: Body[Order]` | JSON request body |
| `@RequestHeader("X-Token") String token` | `token: Header[str]` | HTTP header value |

**Spring example:**
```java
@GetMapping("/search")
public List<Order> search(
    @RequestParam String status,
    @RequestParam(defaultValue = "0") int page,
    @RequestParam(defaultValue = "20") int size
) {
    return service.search(status, page, size);
}
```

**PyFly equivalent:**
```python
@get_mapping("/search")
async def search(
    self,
    status: QueryParam[str],
    page: QueryParam[int] = 0,
    size: QueryParam[int] = 20,
) -> list[dict]:
    return await self._service.search(status, page, size)
```

Python default arguments replace Spring's `defaultValue`.

---

## Exception Handling

### Spring Boot

```java
@ControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleNotFound(ResourceNotFoundException ex) {
        return ResponseEntity.status(404).body(new ErrorResponse(ex.getMessage()));
    }
}
```

### PyFly

PyFly provides automatic exception-to-HTTP mapping through its exception hierarchy. Each exception class has a pre-defined HTTP status code:

```python
from pyfly.kernel import ResourceNotFoundException, ValidationException

# Automatically returns 404
raise ResourceNotFoundException("Order not found", code="ORDER_NOT_FOUND")

# Automatically returns 422
raise ValidationException("Invalid order data", code="VALIDATION_ERROR")
```

| PyFly Exception | HTTP Status |
|----------------|-------------|
| `ValidationException` | 422 |
| `ResourceNotFoundException` | 404 |
| `ConflictException` | 409 |
| `UnauthorizedException` | 401 |
| `ForbiddenException` | 403 |
| `RateLimitException` | 429 |
| `ServiceUnavailableException` | 503 |

**Key difference:** Spring requires you to write `@ControllerAdvice` classes to map exceptions to responses. PyFly's exception hierarchy has this mapping built in — just throw the right exception and the framework produces an RFC 7807-style error response automatically.

You can still add custom exception handlers per controller using `@exception_handler` for cases where you need custom response formatting.

---

## Data Access

### Spring Data JPA

```java
public interface OrderRepository extends JpaRepository<Order, Long> {
    List<Order> findByStatus(String status);
    List<Order> findByStatusAndCustomerName(String status, String name);

    @Query("SELECT o FROM Order o WHERE o.total > :amount")
    List<Order> findExpensiveOrders(@Param("amount") BigDecimal amount);
}
```

### PyFly Data

```python
@repository
class OrderRepository(CrudRepository[Order, int]):
    async def find_by_status(self, status: str) -> list[Order]: ...
    async def find_by_status_and_customer_name(self, status: str, name: str) -> list[Order]: ...

    @query("SELECT o FROM orders WHERE o.total > :amount")
    async def find_expensive_orders(self, amount: float) -> list[Order]: ...
```

**Derived queries** work the same way: define a method signature following the naming convention (`find_by_<field>_and_<field>`), and PyFly generates the query at startup.

**Key difference:** Spring Data uses Java interfaces — methods are abstract and Spring generates implementations at runtime via CGLIB proxying. PyFly uses abstract method signatures (with `...` as the body) on concrete classes. The framework detects these patterns during `ApplicationContext.start()` and generates the query implementations.

### Specifications (Dynamic Queries)

**Spring:**
```java
Specification<Order> spec = (root, query, cb) ->
    cb.and(
        cb.equal(root.get("status"), "ACTIVE"),
        cb.greaterThan(root.get("total"), 100)
    );
List<Order> results = repository.findAll(spec);
```

**PyFly:**
```python
spec = (
    Specification.where(field="status", op="eq", value="ACTIVE")
    .and_where(field="total", op="gt", value=100)
)
results = await repository.find_all_by_spec(spec)
```

### Pagination

**Spring:** `Page<Order> findAll(Pageable pageable)`

**PyFly:**
```python
page: Page[Order] = await repository.find_all_paginated(
    Pageable(page=0, size=20, sort="created_at:desc")
)
# page.content, page.total_elements, page.total_pages, page.number
```

---

## Caching

### Spring Boot

```java
@Cacheable(value = "orders", key = "#id")
public Order findById(Long id) { }

@CacheEvict(value = "orders", key = "#id")
public void deleteOrder(Long id) { }

@CachePut(value = "orders", key = "#order.id")
public Order updateOrder(Order order) { }
```

### PyFly

```python
from pyfly.cache import cacheable, cache_evict, cache_put
from pyfly.cache.adapters.memory import InMemoryCache

cache_backend = InMemoryCache()  # or RedisCacheAdapter

@cacheable(backend=cache_backend, key="order:{id}")
async def find_by_id(self, id: int) -> Order: ...

@cache_evict(backend=cache_backend, key="order:{id}")
async def delete_order(self, id: int) -> None: ...

@cache_put(backend=cache_backend, key="order:{order.id}")
async def update_order(self, order: Order) -> Order: ...
```

The decorator names and behavior map one-to-one. PyFly uses explicit `backend` injection (a `CacheAdapter` instance) rather than named caches. PyFly also provides `@cache` as a simpler alias for `@cacheable`.

**Backend:** Spring auto-configures CacheManager based on classpath. PyFly auto-configures based on installed extras — if `redis` is installed, `RedisCacheAdapter` is used; otherwise `InMemoryCache`. Both can be overridden in configuration.

---

## Scheduling

### Spring Boot

```java
@Scheduled(fixedRate = 5000)
public void pollExternalService() { }

@Scheduled(cron = "0 0 2 * * ?")
public void nightlyCleanup() { }
```

### PyFly

```python
@scheduled(fixed_rate=5.0)
async def poll_external_service(self) -> None: ...

@scheduled(cron="0 2 * * *")
async def nightly_cleanup(self) -> None: ...
```

**Key differences:**
- Spring uses milliseconds (`5000`); PyFly uses seconds (`5.0`)
- Spring cron uses 6 fields (seconds included); PyFly uses standard 5-field cron (minutes, hours, day, month, weekday)
- PyFly scheduling methods are `async`, so they can perform I/O directly without blocking

---

## Aspect-Oriented Programming

### Spring Boot

```java
@Aspect
@Component
public class LoggingAspect {
    @Before("execution(* com.example.service.*.*(..))")
    public void logBefore(JoinPoint joinPoint) {
        logger.info("Calling: {}", joinPoint.getSignature().getName());
    }

    @Around("@annotation(Timed)")
    public Object measureTime(ProceedingJoinPoint pjp) throws Throwable {
        long start = System.nanoTime();
        Object result = pjp.proceed();
        long duration = System.nanoTime() - start;
        logger.info("Execution took {} ms", duration / 1_000_000);
        return result;
    }
}
```

### PyFly

```python
@aspect
@component
class LoggingAspect:
    @before("execution(* my_service.services.*.*(..))")
    async def log_before(self, join_point: JoinPoint) -> None:
        logger.info(f"Calling: {join_point.method_name}")

    @around("annotation(timed)")
    async def measure_time(self, join_point: JoinPoint) -> Any:
        start = time.perf_counter()
        result = await join_point.proceed()
        duration = time.perf_counter() - start
        logger.info(f"Execution took {duration * 1000:.1f} ms")
        return result
```

**Advice types map directly:**

| Spring | PyFly | When it runs |
|--------|-------|-------------|
| `@Before` | `@before` | Before the target method |
| `@AfterReturning` | `@after_returning` | After successful return |
| `@AfterThrowing` | `@after_throwing` | After an exception |
| `@After` | `@after` | After method (always, like `finally`) |
| `@Around` | `@around` | Wraps the method, controls execution |

**Pointcut expressions:** PyFly supports `execution()` for method pattern matching and `annotation()` for targeting decorated methods. The syntax is simplified compared to Spring's AspectJ pointcut language.

---

## Resilience Patterns

### Spring Boot (with Resilience4j)

```java
@CircuitBreaker(name = "orderService", fallbackMethod = "fallback")
@RateLimiter(name = "orderService")
public Order getOrder(Long id) { }
```

### PyFly

```python
from pyfly.resilience import rate_limiter, fallback
from pyfly.client import ServiceClient

# Rate limiting
limiter = rate_limiter(max_calls=100, period=60.0)

@limiter
async def get_order(self, id: int) -> Order: ...

# Circuit breaker (on HTTP clients via builder)
client = (ServiceClient.rest("order-svc")
    .base_url("http://order-svc")
    .circuit_breaker(failure_threshold=5)
    .retry(max_attempts=3)
    .build())

# Fallback
@fallback(fallback_fn=get_cached_order)
async def get_order(self, id: int) -> Order: ...
```

**Additional resilience patterns:**

| Pattern | Spring (Resilience4j) | PyFly |
|---------|----------------------|-------|
| Rate Limiter | `@RateLimiter` | `rate_limiter(max_calls, period)` |
| Circuit Breaker | `@CircuitBreaker` | `CircuitBreaker(failure_threshold, recovery_timeout)` |
| Bulkhead | `@Bulkhead` | `bulkhead(max_concurrent)` |
| Time Limiter | `@TimeLimiter` | `time_limiter(timeout)` |
| Retry | `@Retry` | `RetryPolicy(max_retries, backoff)` |
| Fallback | `fallbackMethod` | `@fallback(fallback_fn)` |

---

## Observability

### Spring Boot Actuator

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics
```

### PyFly Actuator

```yaml
pyfly:
  web:
    actuator:
      enabled: true
```

| Spring Actuator | PyFly Actuator |
|----------------|----------------|
| `/actuator/health` | `/actuator/health` |
| `/actuator/info` | `/actuator/info` |
| `/actuator/beans` | `/actuator/beans` |
| `/actuator/env` | `/actuator/env` |

### Metrics

**Spring:** Uses Micrometer (Prometheus registry, `@Timed` annotation)

**PyFly:** Uses `MetricsRegistry` with Prometheus backend:

```python
from pyfly.observability import timed, counted, MetricsRegistry

@timed("order_service_find")
async def find_order(self, id: int) -> Order: ...

@counted("orders_created")
async def create_order(self, data: dict) -> Order: ...
```

---

## Messaging

### Spring Boot (with Spring Kafka)

```java
@KafkaListener(topics = "orders", groupId = "order-service")
public void handleOrder(OrderEvent event) { }

@Autowired  // Spring field injection
private KafkaTemplate<String, OrderEvent> kafkaTemplate;

public void publishOrder(OrderEvent event) {
    kafkaTemplate.send("orders", event);
}
```

### PyFly

```python
from pyfly.messaging import message_listener
from pyfly.eda import event_publisher, EventEnvelope

@message_listener(topic="orders", group_id="order-service")
async def handle_order(self, event: dict) -> None: ...

@event_publisher
class OrderPublisher:
    async def publish_order(self, event: EventEnvelope) -> None:
        await self._event_bus.publish(event)
```

**Key difference:** PyFly separates **messaging** (Kafka/RabbitMQ transport) from **events** (domain event bus). The messaging module handles broker communication; the EDA module provides the event bus abstraction. This means you can publish domain events within a monolith using `InMemoryEventBus` and later switch to Kafka by changing the adapter — no code changes needed.

---

## Quick Reference Table

A complete mapping of Spring Boot concepts to PyFly equivalents:

| Spring Boot | PyFly | Notes |
|-------------|-------|-------|
| `@SpringBootApplication` | `@pyfly_application` | Entry point decorator |
| `@Component` | `@component` | Generic managed bean |
| `@Service` | `@service` | Business logic |
| `@Repository` | `@repository` | Data access |
| `@RestController` | `@rest_controller` | REST endpoints |
| `@Configuration` + `@Bean` | `@configuration` + `@bean` | Bean factories |
| `@Autowired` | Constructor injection (automatic) + `Autowired()` field injection | Type-hint based |
| `@Qualifier` | `Qualifier("name")` with `Annotated` | Named bean selection |
| `@Primary` | `@primary` | Default implementation |
| `@ConditionalOnProperty` | `@conditional_on_property` | Config-based activation |
| `@ConditionalOnClass` | `@conditional_on_class` | Library detection |
| `@ConditionalOnMissingBean` | `@conditional_on_missing_bean` | Missing bean check |
| `@ConditionalOnBean` | `@conditional_on_bean` | Bean presence check |
| `@PostConstruct` | `@post_construct` | Initialization hook |
| `@PreDestroy` | `@pre_destroy` | Cleanup hook |
| `@Order` | `@order` | Execution priority |
| `application.yml` | `pyfly.yaml` | Configuration file |
| `@ConfigurationProperties` | `@config_properties` | Typed config binding |
| Spring Profiles | PyFly Profiles | Environment overlays |
| `@GetMapping` | `@get_mapping` | HTTP GET handler |
| `@PostMapping` | `@post_mapping` | HTTP POST handler |
| `@PutMapping` | `@put_mapping` | HTTP PUT handler |
| `@DeleteMapping` | `@delete_mapping` | HTTP DELETE handler |
| `@PatchMapping` | `@patch_mapping` | HTTP PATCH handler |
| `@RequestBody` | `Body[T]` | JSON request body |
| `@PathVariable` | Plain parameter or `PathVar[T]` | URL path parameter |
| `@RequestParam` | `QueryParam[T]` | Query string parameter |
| `@RequestHeader` | `Header[T]` | HTTP header value |
| `@ControllerAdvice` | `@exception_handler` | Exception handling |
| `@Scheduled(fixedRate)` | `@scheduled(fixed_rate)` | Periodic tasks |
| `@Scheduled(cron)` | `@scheduled(cron)` | Cron-based scheduling |
| `@Cacheable` | `@cacheable` | Method caching |
| `@CacheEvict` | `@cache_evict` | Cache eviction |
| `@CachePut` | `@cache_put` | Cache update |
| `@Aspect` | `@aspect` | AOP aspect |
| `@Before` | `@before` | Before advice |
| `@After` | `@after` | After advice |
| `@Around` | `@around` | Around advice |
| `@AfterReturning` | `@after_returning` | After-returning advice |
| `@AfterThrowing` | `@after_throwing` | After-throwing advice |
| `JpaRepository` | `CrudRepository` / `Repository` | CRUD operations |
| `findByXAndY` | `find_by_x_and_y` | Derived queries |
| `@Query` | `@query` | Custom queries |
| `Specification` | `Specification` | Dynamic query predicates |
| `Page<T>` | `Page[T]` | Paginated results |
| `Pageable` | `Pageable` | Pagination request |
| Actuator `/health` | Actuator `/actuator/health` | Health checks |
| Actuator `/info` | Actuator `/actuator/info` | App metadata |
| Actuator `/beans` | Actuator `/actuator/beans` | Bean registry |
| `CircuitBreaker` | `CircuitBreaker` | Resilience pattern |
| `@RateLimiter` | `rate_limiter` | Rate limiting |
| `@Bulkhead` | `bulkhead` | Concurrency limiting |
| `@TimeLimiter` | `time_limiter` | Operation timeout |
| `@Retry` | `RetryPolicy` | Retry with backoff |
| `KafkaTemplate` | `MessageBrokerPort` | Message publishing |
| `@KafkaListener` | `@message_listener` | Message consumption |
| `ApplicationEvent` | `EventEnvelope` | Domain events |
| `@EventListener` | `@event_listener` | Event handling |
| Micrometer `@Timed` | `@timed` | Method timing |
| Micrometer `@Counted` | `@counted` | Invocation counting |

---

*For detailed guides on each topic, see the [Documentation Index](index.md).*
