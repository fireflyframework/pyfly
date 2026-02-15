# Data Relational Guide

> **PyFly Data** follows the Spring Data umbrella architecture. The framework is organized into two layers:
>
> | Layer | Package | Purpose |
> |-------|---------|---------|
> | **Data Commons** | `pyfly.data` | Shared abstractions — `RepositoryPort[T, ID]`, `Page`, `Pageable`, `Sort`, `QueryMethodParser`, `QueryMethodCompilerPort` |
> | **SQLAlchemy Adapter** | `pyfly.data.relational.sqlalchemy` | Concrete adapter — `Base`, `BaseEntity`, `Repository[T, ID]`, `Specification`, `FilterOperator`, `FilterUtils`, `@query`, `reactive_transactional` |
>
> This guide covers the **relational** layer and its default **SQLAlchemy adapter**. For document databases, see the [Data Document Guide](data-document.md). Both adapters share the same commons layer and can coexist in the same project.
>
> **Hexagonal by design:** your services depend on `RepositoryPort[T, ID]` (the port), never on `Repository[T, ID]` (the adapter). SQLAlchemy is the default relational adapter today — but the layer is designed so any relational backend (Tortoise ORM, Django ORM, etc.) can be added by implementing the same ports.

PyFly Data Relational implements the Repository pattern with Spring Data-style derived query methods, composable specifications, pagination, entity mapping, and declarative transaction management. Framework-agnostic ports define the repository and session contracts; the SQLAlchemy adapter provides the concrete implementation.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Entity Definition](#entity-definition)
  - [Base (DeclarativeBase)](#base-declarativebase)
  - [BaseEntity: Audit Trail Fields](#baseentity-audit-trail-fields)
  - [Defining Your Own Entities](#defining-your-own-entities)
- [Repository Pattern](#repository-pattern)
  - [Repository Class](#repository-class)
  - [Creating a Repository](#creating-a-repository)
  - [CRUD Methods Reference](#crud-methods-reference)
- [Repository Ports](#repository-ports)
  - [RepositoryPort](#repositoryport)
  - [SessionPort](#sessionport)
  - [CrudRepository](#crudrepository)
  - [PagingRepository](#pagingrepository)
- [Derived Query Methods](#derived-query-methods)
  - [Naming Convention](#naming-convention)
  - [Prefixes](#prefixes)
  - [Operators](#operators)
  - [Connectors](#connectors)
  - [Ordering](#ordering)
  - [Complete Derived Query Examples](#complete-derived-query-examples)
- [Custom Queries with @query](#custom-queries-with-query)
  - [JPQL-Like Syntax](#jpql-like-syntax)
  - [Native SQL](#native-sql)
  - [Return Type Inference](#return-type-inference)
  - [JPQL Transpilation Details](#jpql-transpilation-details)
- [Specifications](#specifications)
  - [Creating Specifications](#creating-specifications)
  - [Combining Specifications](#combining-specifications)
  - [Using Specifications with Repositories](#using-specifications-with-repositories)
- [FilterOperator](#filteroperator)
  - [Available Operators](#available-operators)
  - [Composing Filters](#composing-filters)
- [FilterUtils: Query by Example](#filterutils-query-by-example)
- [Pagination](#pagination)
  - [Pageable: Requesting a Page](#pageable-requesting-a-page)
  - [Sort and Order](#sort-and-order)
  - [Page: The Result](#page-the-result)
  - [Paginated Queries](#paginated-queries)
  - [Paginated Specification Queries](#paginated-specification-queries)
- [Entity Mapping](#entity-mapping)
  - [Basic Mapping](#basic-mapping)
  - [Custom Field Mapping](#custom-field-mapping)
  - [Transformers](#transformers)
  - [Excluding Fields](#excluding-fields)
  - [Mapping Lists](#mapping-lists)
- [Transaction Management](#transaction-management)
- [RepositoryBeanPostProcessor](#repositorybeanpostprocessor)
  - [How It Works](#how-it-works)
  - [Stub Detection](#stub-detection)
- [QueryMethodParser and QueryMethodCompiler](#querymethodparser-and-querymethodcompiler)
  - [Parser Internals](#parser-internals)
  - [Compiler Internals](#compiler-internals)
- [Complete CRUD Example](#complete-crud-example)

---

## Architecture Overview

The data module follows a hexagonal architecture with two distinct layers:

### Layer 1: Data Commons (`pyfly.data`)

Framework-agnostic types shared by **all** data adapters (relational and document). These contain zero backend-specific code:

```python
from pyfly.data import (
    Page, Pageable, Sort, Order,       # Pagination
    Mapper,                             # Entity ↔ DTO mapping
    RepositoryPort, SessionPort,        # Port interfaces
    CrudRepository, PagingRepository,   # Extended port interfaces
    QueryMethodParser,                  # Derived query parsing (shared)
    QueryMethodCompilerPort,            # Compiler contract
)
```

Your service layer should depend on these ports — never on the adapter directly.

### Layer 2: SQLAlchemy Adapter (`pyfly.data.relational.sqlalchemy`)

All concrete types live in the SQLAlchemy adapter package. The namespace `pyfly.data.relational` is a pass-through and does not re-export anything.

```python
from pyfly.data.relational.sqlalchemy import (
    Base, BaseEntity,                   # SQLAlchemy entity base classes
    Repository,                         # Repository[T, ID] implementation
    Specification,                      # Composable query predicates
    FilterOperator, FilterUtils,        # Query-by-example utilities
    QueryExecutor, query,               # Custom @query decorator
    QueryMethodCompiler,                # Derived query → SQLAlchemy compiler
    RepositoryBeanPostProcessor,        # Auto-wires query methods
    reactive_transactional,             # Declarative transaction management
)
```

> **Note:** Always import concrete types from `pyfly.data.relational.sqlalchemy`. The `pyfly.data.relational` namespace is reserved for future cross-adapter abstractions and does not export any types.

---

## Entity Definition

### Base (DeclarativeBase)

PyFly exports a pre-configured SQLAlchemy `DeclarativeBase`:

```python
from pyfly.data.relational.sqlalchemy import Base
```

Use `Base` directly when you need SQLAlchemy entities without the built-in audit trail fields.

### BaseEntity: Audit Trail Fields

`BaseEntity` extends `Base` and provides a UUID primary key plus four audit trail columns. All domain entities should inherit from this class:

```python
from pyfly.data.relational.sqlalchemy import BaseEntity
```

**Inherited fields:**

| Field        | Type              | Column Type        | Description                          |
|--------------|-------------------|--------------------|--------------------------------------|
| `id`         | `Mapped[UUID]`    | Primary key        | Auto-generated UUID v4               |
| `created_at` | `Mapped[datetime]`| `DateTime(tz=True)`| Set automatically on insert          |
| `updated_at` | `Mapped[datetime]`| `DateTime(tz=True)`| Set on insert, updated on every save |
| `created_by` | `Mapped[str\|None]`| `String(255)`     | Creator identifier (default `None`)  |
| `updated_by` | `Mapped[str\|None]`| `String(255)`     | Updater identifier (default `None`)  |

`BaseEntity` is declared with `__abstract__ = True`, so it does not create its own database table.

### Defining Your Own Entities

Extend `BaseEntity` and declare your domain columns:

```python
from pyfly.data.relational.sqlalchemy import BaseEntity
from sqlalchemy import String, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column


class Order(BaseEntity):
    __tablename__ = "orders"

    customer_id: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    total: Mapped[float] = mapped_column(Float, default=0.0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
```

This entity will have all five inherited fields (`id`, `created_at`, `updated_at`, `created_by`, `updated_by`) plus your four custom columns.

---

## Repository Pattern

### Repository Class

The `Repository[T, ID]` class provides generic async CRUD operations for any SQLAlchemy model. It wraps a SQLAlchemy `AsyncSession` and the entity model type. The two type parameters are:

- **T** — The entity type (any SQLAlchemy model, including `BaseEntity` subclasses or plain `Base` subclasses)
- **ID** — The primary key type (e.g. `UUID`, `int`, `str`)

```python
from uuid import UUID
from pyfly.data.relational.sqlalchemy import Repository

repo = Repository[Order, UUID](Order, session)
order = await repo.save(Order(customer_id="abc", status="PENDING"))
found = await repo.find_by_id(order.id)
```

### Creating a Repository

Subclass `Repository[T, ID]` and register it as a bean with the `@repository` stereotype:

```python
from uuid import UUID
from pyfly.data.relational.sqlalchemy import Repository
from pyfly.container import repository as repo_stereotype
from sqlalchemy.ext.asyncio import AsyncSession


@repo_stereotype
class OrderRepository(Repository[Order, UUID]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Order, session)
```

For entities with integer primary keys:

```python
@repo_stereotype
class ProductRepository(Repository[Product, int]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Product, session)
```

The `session` parameter is injected by the DI container.

### CRUD Methods Reference

| Method                                           | Return Type  | Description                                    |
|--------------------------------------------------|--------------|------------------------------------------------|
| `save(entity)`                                   | `T`          | Insert or update; flushes and refreshes        |
| `find_by_id(id: ID)`                             | `T \| None`  | Find by primary key                            |
| `find_all(**filters)`                             | `list[T]`    | Find all, optionally filtered by column values |
| `delete(id: ID)`                                  | `None`       | Delete by primary key (no-op if not found)     |
| `count()`                                         | `int`        | Count all entities in the table                |
| `exists(id: ID)`                                  | `bool`       | Check if an entity with this ID exists         |
| `find_paginated(page, size, pageable)`            | `Page[T]`    | Paginated query with optional sorting          |
| `find_all_by_spec(spec)`                          | `list[T]`    | Find all matching a Specification              |
| `find_all_by_spec_paged(spec, pageable)`          | `Page[T]`    | Paginated query with Specification + sorting   |

**save()** calls `session.add()`, then `session.flush()` and `session.refresh()` to ensure the returned entity has all database-generated values (ID, defaults, etc.).

**find_all()** accepts keyword arguments that are translated into equality filters:

```python
orders = await repo.find_all(status="PENDING", customer_id="abc")
# Equivalent to: SELECT * FROM orders WHERE status = 'PENDING' AND customer_id = 'abc'
```

**delete()** looks up the entity first and deletes it if found. If not found, it is a no-op.

---

## Repository Ports

For hexagonal architecture, your service layer should depend on ports rather than the concrete `Repository` class.

### RepositoryPort

The base repository interface:

```python
class RepositoryPort(Protocol[T]):
    async def save(self, entity: T) -> T: ...
    async def find_by_id(self, id: UUID) -> T | None: ...
    async def find_all(self, **filters: Any) -> list[T]: ...
    async def delete(self, id: UUID) -> None: ...
    async def count(self) -> int: ...
    async def exists(self, id: UUID) -> bool: ...
```

### SessionPort

Abstract session interface for transaction management:

```python
class SessionPort(Protocol):
    async def begin(self) -> Any: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
```

### CrudRepository

Spring Data-style CRUD interface with type parameters for both entity and ID:

```python
class CrudRepository(Protocol[T, ID]):
    async def save(self, entity: T) -> T: ...
    async def find_by_id(self, id: ID) -> T | None: ...
    async def find_all(self) -> list[T]: ...
    async def delete(self, entity: T) -> None: ...
    async def delete_by_id(self, id: ID) -> None: ...
    async def count(self) -> int: ...
    async def exists_by_id(self, id: ID) -> bool: ...
```

### PagingRepository

Extends `CrudRepository` with pagination:

```python
class PagingRepository(CrudRepository[T, ID], Protocol[T, ID]):
    async def find_all_paged(
        self, page: int = 1, size: int = 20, sort: list[str] | None = None
    ) -> Page[T]: ...
```

---

## Derived Query Methods

PyFly can automatically generate query implementations from method names, following the Spring Data naming convention. You define stub methods on your repository and the `RepositoryBeanPostProcessor` compiles them into real SQLAlchemy queries at startup.

### Naming Convention

```
<prefix>_<field>[_<operator>][_<connector>_<field>[_<operator>]]*[_order_by_<field>_<direction>]*
```

### Prefixes

| Prefix       | Return Type | Description                            |
|--------------|-------------|----------------------------------------|
| `find_by_`   | `list[T]`   | Find all matching entities             |
| `count_by_`  | `int`       | Count matching entities                |
| `exists_by_` | `bool`      | Check if any entity matches            |
| `delete_by_` | `int`       | Delete matching entities (return count)|

### Operators

Operators are suffixed to field names. They are checked longest-first to avoid partial matches (e.g., `_greater_than_equal` before `_greater_than`).

| Suffix                 | Operator      | SQL Equivalent       | Args  |
|------------------------|---------------|----------------------|-------|
| *(none)*               | `eq`          | `=`                  | 1     |
| `_greater_than`        | `gt`          | `>`                  | 1     |
| `_less_than`           | `lt`          | `<`                  | 1     |
| `_greater_than_equal`  | `gte`         | `>=`                 | 1     |
| `_less_than_equal`     | `lte`         | `<=`                 | 1     |
| `_between`             | `between`     | `BETWEEN ? AND ?`    | 2     |
| `_like`                | `like`        | `LIKE ?`             | 1     |
| `_containing`          | `containing`  | `LIKE %?%`           | 1     |
| `_in`                  | `in`          | `IN (?)`             | 1 (list) |
| `_not`                 | `not`         | `!=`                 | 1     |
| `_is_null`             | `is_null`     | `IS NULL`            | 0     |
| `_is_not_null`         | `is_not_null` | `IS NOT NULL`        | 0     |

### Connectors

Connect multiple predicates with `_and_` or `_or_`:

```python
# AND: status = ? AND customer_id = ?
async def find_by_status_and_customer_id(self, status: str, customer_id: str) -> list[Order]: ...

# OR: status = ? OR role = ?
async def find_by_status_or_role(self, status: str, role: str) -> list[User]: ...
```

### Ordering

Append `_order_by_{field}_{asc|desc}` to control result ordering. Multiple sort fields can be chained:

```python
# ORDER BY created_at DESC
async def find_by_status_order_by_created_at_desc(self, status: str) -> list[Order]: ...

# ORDER BY name ASC, created_at DESC
async def find_by_active_order_by_name_asc_created_at_desc(self, active: bool) -> list[User]: ...
```

### Complete Derived Query Examples

```python
@repo_stereotype
class OrderRepository(Repository[Order, UUID]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Order, session)

    # Equals (default operator)
    async def find_by_status(self, status: str) -> list[Order]: ...

    # Multiple conditions with AND
    async def find_by_customer_id_and_status(
        self, customer_id: str, status: str
    ) -> list[Order]: ...

    # Greater than
    async def find_by_total_greater_than(self, min_total: float) -> list[Order]: ...

    # Between (takes 2 arguments)
    async def find_by_total_between(self, low: float, high: float) -> list[Order]: ...

    # LIKE pattern
    async def find_by_customer_id_like(self, pattern: str) -> list[Order]: ...

    # Contains (wraps value in %)
    async def find_by_customer_id_containing(self, fragment: str) -> list[Order]: ...

    # IN a list
    async def find_by_status_in(self, statuses: list[str]) -> list[Order]: ...

    # IS NULL / IS NOT NULL (zero arguments consumed)
    async def find_by_deleted_at_is_null(self) -> list[Order]: ...
    async def find_by_email_is_not_null(self) -> list[User]: ...

    # COUNT prefix
    async def count_by_status(self, status: str) -> int: ...

    # EXISTS prefix
    async def exists_by_customer_id(self, customer_id: str) -> bool: ...

    # DELETE prefix (returns number of rows deleted)
    async def delete_by_status(self, status: str) -> int: ...

    # With ordering
    async def find_by_status_order_by_created_at_desc(
        self, status: str
    ) -> list[Order]: ...

    # Complex: AND + OR + ordering
    async def find_by_status_and_customer_id_order_by_total_desc(
        self, status: str, customer_id: str
    ) -> list[Order]: ...
```

Each of these method bodies should be a stub (`...` or `pass`). The `RepositoryBeanPostProcessor` detects them and replaces them with real implementations at startup.

---

## Custom Queries with @query

For complex queries that cannot be expressed through method naming conventions, use the `@query` decorator:

```python
from pyfly.data.relational.sqlalchemy import query
```

### JPQL-Like Syntax

By default, `@query` accepts a JPQL-like query string that is transpiled to SQL at startup:

```python
@repo_stereotype
class OrderRepository(Repository[Order, UUID]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Order, session)

    @query("SELECT o FROM Order o WHERE o.status = :status AND o.total > :min_total")
    async def find_expensive_orders(
        self, status: str, min_total: float
    ) -> list[Order]: ...

    @query("SELECT COUNT(o) FROM Order o WHERE o.role = :role")
    async def count_by_role(self, role: str) -> int: ...
```

Named parameters (`:param_name`) are bound from the method's keyword arguments.

### Native SQL

Set `native=True` for raw SQL queries:

```python
@query("SELECT * FROM orders WHERE status = :status", native=True)
async def find_by_status_native(self, status: str) -> list[Order]: ...
```

### Return Type Inference

The `QueryExecutor` infers the return type from the query shape:

| Query Pattern              | Return Type    |
|----------------------------|----------------|
| `SELECT COUNT(...)`        | `int`          |
| Query containing `EXISTS`  | `bool`         |
| All other `SELECT` queries | `list[entity]` |

### JPQL Transpilation Details

The lightweight JPQL-to-SQL transpiler performs these transformations:

1. `FROM Entity alias` becomes `FROM <tablename>` (alias is removed)
2. `SELECT alias` becomes `SELECT *`
3. `COUNT(alias)` becomes `COUNT(*)`
4. `alias.field` references become just `field` (alias prefix stripped)
5. Boolean literals `= true` / `= false` become `= 1` / `= 0`

Example transpilation:

```
JPQL:  SELECT u FROM User u WHERE u.email LIKE :pattern AND u.active = true
SQL:   SELECT * FROM users WHERE email LIKE :pattern AND active = 1
```

---

## Specifications

Specifications provide composable, type-safe query predicates inspired by Spring Data's Specification pattern. They let you build arbitrarily complex WHERE clauses from small, reusable building blocks.

> **Commons port:** The SQLAlchemy `Specification[T]` subclasses the generic `Specification[T, Q]` ABC from `pyfly.data.specification`. This means SQLAlchemy specifications are polymorphic with the commons port — code that accepts `pyfly.data.Specification` will work with the SQLAlchemy adapter. See the [Specification Port](data.md#specification-port) section in the Data Commons guide.

### Creating Specifications

A `Specification[T]` wraps a callable that takes an entity class (`root`) and a SQLAlchemy `Select` statement, and returns a modified `Select`:

```python
from pyfly.data.relational.sqlalchemy import Specification

# Inline specification
active = Specification(lambda root, q: q.where(root.active == True))
admin = Specification(lambda root, q: q.where(root.role == "admin"))
```

### Combining Specifications

Specifications support Python's standard operators for composition:

```python
# AND: both conditions must match
active_admins = active & admin

# OR: either condition may match
active_or_admin = active | admin

# NOT: negate a specification
inactive = ~active

# Complex combinations with parentheses
complex_spec = (active & admin) | ~admin
```

**How combination works internally:**

- `&` (AND): Chains the two predicates sequentially. SQLAlchemy naturally combines successive `.where()` calls with AND.
- `|` (OR): Applies each predicate independently, extracts the `whereclause` from each, and combines them using `sqlalchemy.or_()`.
- `~` (NOT): Applies the predicate, extracts the `whereclause`, and wraps it with `sqlalchemy.not_()`.

### Using Specifications with Repositories

```python
# Find all matching a specification
orders = await repo.find_all_by_spec(active & admin)

# Find with pagination
from pyfly.data import Pageable, Sort

pageable = Pageable.of(page=1, size=20, sort=Sort.by("created_at").descending())
page = await repo.find_all_by_spec_paged(active & admin, pageable)
```

---

## FilterOperator

`FilterOperator` provides a library of static factory methods for creating common `Specification` predicates without writing lambdas.

### Available Operators

| Method                            | SQL Equivalent                | Arguments      |
|-----------------------------------|-------------------------------|----------------|
| `eq(field, value)`                | `field = value`               | field, value   |
| `neq(field, value)`               | `field != value`              | field, value   |
| `gt(field, value)`                | `field > value`               | field, value   |
| `gte(field, value)`               | `field >= value`              | field, value   |
| `lt(field, value)`                | `field < value`               | field, value   |
| `lte(field, value)`               | `field <= value`              | field, value   |
| `like(field, pattern)`            | `field LIKE pattern`          | field, pattern |
| `contains(field, value)`          | `field LIKE '%value%'`        | field, value   |
| `in_list(field, values)`          | `field IN (values)`           | field, list    |
| `is_null(field)`                  | `field IS NULL`               | field          |
| `is_not_null(field)`              | `field IS NOT NULL`           | field          |
| `between(field, low, high)`       | `field BETWEEN low AND high`  | field, low, high|

### Composing Filters

Every `FilterOperator` method returns a `Specification`, so they can be composed with `&`, `|`, and `~`:

```python
from pyfly.data.relational.sqlalchemy import FilterOperator

# Adults between 18 and 65
age_filter = FilterOperator.gte("age", 18) & FilterOperator.lt("age", 65)

# Active users with a verified email
user_filter = FilterOperator.eq("active", True) & FilterOperator.is_not_null("email_verified_at")

# Premium or VIP customers
tier_filter = FilterOperator.in_list("tier", ["PREMIUM", "VIP"])

# Combine everything
final_spec = age_filter & user_filter & tier_filter
results = await repo.find_all_by_spec(final_spec)
```

---

## FilterUtils: Query by Example

> **Commons port:** `FilterUtils` extends the `BaseFilterUtils` ABC from `pyfly.data.filter`. The `by()`, `from_dict()`, and `from_example()` algorithms are inherited from the base class — `FilterUtils` only implements the adapter-specific hooks `_create_eq()` and `_create_noop()`. See the [BaseFilterUtils Port](data.md#basefilterutils-port) section in the Data Commons guide.

`FilterUtils` generates `Specification` objects from various input formats, providing a Pythonic take on Spring Data's Query by Example pattern.

```python
from pyfly.data.relational.sqlalchemy import FilterUtils

# From keyword arguments (all eq, ANDed together)
spec = FilterUtils.by(name="Alice", active=True)
results = await repo.find_all_by_spec(spec)

# From a dictionary (None values are automatically skipped)
filters = {"role": "admin", "name": None, "active": True}
spec = FilterUtils.from_dict(filters)
# Produces: role = 'admin' AND active = True (name is skipped)

# From an example object (dataclass or plain object)
# Non-None fields become equality predicates
from dataclasses import dataclass

@dataclass
class UserFilter:
    role: str | None = None
    active: bool | None = None

example = UserFilter(role="admin")
spec = FilterUtils.from_example(example)
# Produces: role = 'admin' (active is None, so skipped)
```

**FilterUtils methods:**

| Method                    | Input                | Behavior                                    |
|---------------------------|----------------------|---------------------------------------------|
| `by(**kwargs)`            | Keyword arguments    | All eq, ANDed together                      |
| `from_dict(filters)`      | `dict[str, Any]`     | All eq, ANDed; `None` values skipped        |
| `from_example(example)`   | Dataclass or object  | Non-`None` fields become eq predicates      |

---

## Pagination

### Pageable: Requesting a Page

`Pageable` is a frozen dataclass that encapsulates pagination parameters:

```python
from pyfly.data import Pageable, Sort, Order as SortOrder

# Simple pagination
pageable = Pageable.of(page=1, size=20)

# With sorting
pageable = Pageable.of(page=1, size=20, sort=Sort.by("created_at").descending())

# Unpaged (fetch all results)
pageable = Pageable.unpaged()
```

**Pageable fields and properties:**

| Field/Property | Type    | Description                                         |
|----------------|---------|-----------------------------------------------------|
| `page`         | `int`   | Page number (1-based, must be >= 1)                  |
| `size`         | `int`   | Maximum items per page (must be >= 1)                |
| `sort`         | `Sort`  | Sort criteria                                        |
| `offset`       | `int`   | Calculated SQL offset: `(page - 1) * size`           |
| `is_paged`     | `bool`  | `True` for normal pagination, `False` for unpaged    |

**Navigation methods:**

```python
next_page = pageable.next()        # Pageable for page + 1
prev_page = pageable.previous()    # Pageable for page - 1 (minimum page 1)
```

**Validation:** `Pageable.__post_init__` raises `ValueError` if `page < 1` or `size < 1` (except for the unpaged sentinel).

### Sort and Order

`Sort` is a collection of `Order` objects:

```python
from pyfly.data import Sort, Order as SortOrder

# Sort by a single field ascending
sort = Sort.by("name")

# Sort by a single field descending
sort = Sort.by("name").descending()

# Multiple sort fields
sort = Sort(orders=(
    SortOrder.desc("created_at"),
    SortOrder.asc("name"),
))

# Combine sorts
sort1 = Sort.by("name")
sort2 = Sort.by("created_at").descending()
combined = sort1.and_then(sort2)

# No sorting
sort = Sort.unsorted()

# Flip all directions
reversed_sort = sort.descending()  # All orders become desc
```

`Order` is a single sort directive:

```python
order_asc = SortOrder.asc("name")       # Order(property="name", direction="asc")
order_desc = SortOrder.desc("created_at") # Order(property="created_at", direction="desc")
```

### Page: The Result

`Page[T]` is a frozen dataclass returned by paginated queries:

```python
page = await repo.find_paginated(page=1, size=20)

page.items          # list[Order] -- the items on this page
page.total          # int -- total items across all pages
page.page           # int -- current page number (1-based)
page.size           # int -- maximum items per page
page.total_pages    # int -- total number of pages (ceil(total / size))
page.has_next       # bool -- whether there is a next page
page.has_previous   # bool -- whether there is a previous page
```

**Transforming items:**

The `map()` method transforms each item while preserving pagination metadata:

```python
dto_page: Page[OrderDTO] = page.map(
    lambda order: OrderDTO(id=str(order.id), status=order.status)
)
```

### Paginated Queries

```python
# Basic pagination
page = await repo.find_paginated(page=1, size=20)

# With Pageable (overrides page/size and adds sorting)
pageable = Pageable.of(page=2, size=10, sort=Sort.by("name"))
page = await repo.find_paginated(pageable=pageable)
```

When `pageable` is provided, its `page`, `size`, and `sort` override the primitive `page` and `size` arguments.

### Paginated Specification Queries

```python
spec = FilterOperator.eq("status", "ACTIVE")
pageable = Pageable.of(page=1, size=20, sort=Sort.by("created_at").descending())

page = await repo.find_all_by_spec_paged(spec, pageable)
# Returns Page[Order] with filtered, sorted, paginated results
```

The implementation:
1. Applies the specification's predicate to get the filtered query.
2. Counts total matching rows via a subquery.
3. Applies sort orders from `Pageable.sort`.
4. Applies `offset` and `limit` for pagination.

---

## Entity Mapping

The `Mapper` class provides type-to-type mapping between entities and DTOs, inspired by MapStruct. It automatically matches fields by name and supports custom renaming, transformers, and exclusion.

### Basic Mapping

```python
from pyfly.data import Mapper
from dataclasses import dataclass


@dataclass
class OrderDTO:
    id: str
    status: str
    total: float


mapper = Mapper()
dto = mapper.map(order_entity, OrderDTO)
# Matches fields by name: id, status, total
```

### Custom Field Mapping

When source and destination field names differ:

```python
mapper = Mapper()
mapper.add_mapping(
    Order, OrderDTO,
    field_map={"customer_id": "buyer_id"},
    # Source field "customer_id" maps to destination field "buyer_id"
)
dto = mapper.map(order, OrderDTO)
```

The `field_map` uses `{source_name: dest_name}` format. Reverse lookup is performed: for each destination field, the mapper checks if any source field maps to it.

### Transformers

Apply functions to transform field values during mapping:

```python
mapper.add_mapping(
    Order, OrderDTO,
    transformers={
        "status": str.upper,        # "pending" -> "PENDING"
        "total": lambda v: round(v, 2),
    },
)
```

Transformers are keyed by destination field name and applied after the value is retrieved from the source.

### Excluding Fields

Omit specific fields from the mapping:

```python
mapper.add_mapping(
    Order, OrderDTO,
    exclude={"internal_notes", "audit_log"},
)
```

### Mapping Lists

```python
dtos = mapper.map_list(orders, OrderDTO)
# Equivalent to [mapper.map(o, OrderDTO) for o in orders]
```

**`add_mapping()` full parameter reference:**

| Parameter      | Type                               | Description                                    |
|----------------|------------------------------------|------------------------------------------------|
| `source_type`  | `type[S]`                          | Source class to map from                        |
| `dest_type`    | `type[D]`                          | Destination class to map to                     |
| `field_map`    | `dict[str, str] \| None`           | `{source_field: dest_field}` renaming           |
| `transformers` | `dict[str, Callable] \| None`      | `{dest_field: transform_fn}` value transformers |
| `exclude`      | `set[str] \| None`                 | Destination fields to skip                      |

The mapper supports both dataclasses and plain objects. Source field extraction uses `dataclasses.asdict()` for dataclasses and `vars()` for other objects. Destination field discovery uses `dataclasses.fields()` or `get_type_hints()`.

---

## Transaction Management

The `@reactive_transactional` decorator provides declarative async transaction management:

```python
from pyfly.data.relational.sqlalchemy import reactive_transactional
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

session_factory: async_sessionmaker[AsyncSession] = ...


@reactive_transactional(session_factory)
async def create_order(session: AsyncSession, customer_id: str) -> Order:
    order = Order(customer_id=customer_id, status="PENDING")
    session.add(order)
    return order
    # Transaction is automatically committed on success
    # Transaction is automatically rolled back on exception
```

**How it works:**
1. Opens a new `AsyncSession` from the `session_factory`.
2. Begins a transaction with `session.begin()`.
3. Calls the wrapped function with the session as the first argument.
4. On success: the transaction is committed (via the `async with` context manager).
5. On exception: the transaction is rolled back and the exception is re-raised.

The decorated function's original arguments are passed after the injected `session`:

```python
@reactive_transactional(session_factory)
async def transfer_funds(session: AsyncSession, from_id: str, to_id: str, amount: float):
    # session is injected; from_id, to_id, amount are passed through
    ...

# Call it without the session argument:
await transfer_funds("acc-1", "acc-2", 100.0)
```

---

## RepositoryBeanPostProcessor

The `RepositoryBeanPostProcessor` is a `BeanPostProcessor` that runs after each repository bean is initialized. It scans the repository class for stub methods and replaces them with real query implementations.

### How It Works

The `after_init(bean, bean_name)` method:

1. Checks if the bean is an instance of `Repository`. If not, it is returned unchanged.
2. Gets the entity type from `bean._model`.
3. Iterates over all attributes defined on the bean's class (not inherited from `Repository`).
4. For `@query`-decorated methods: compiles them via `QueryExecutor.compile_query_method()` and replaces the stub with a wrapper that injects `bean._session`.
5. For derived query methods (`find_by_*`, `count_by_*`, `exists_by_*`, `delete_by_*`): checks if the method is a stub, parses the method name via `QueryMethodParser.parse()`, compiles it via `QueryMethodCompiler.compile()`, and replaces the stub with a wrapper.

### Stub Detection

A method is considered a stub when its code object contains no meaningful constants beyond `None` and `Ellipsis`. This covers both forms:

```python
async def find_by_status(self, status: str) -> list[Order]: ...    # Ellipsis stub
async def find_by_status(self, status: str) -> list[Order]: pass   # Pass stub
```

Register the post-processor in your application context:

```python
from pyfly.data.relational.sqlalchemy import RepositoryBeanPostProcessor

context.register_post_processor(RepositoryBeanPostProcessor())
```

---

## QueryMethodParser and QueryMethodCompiler

These two classes form the internal pipeline that powers derived query methods.

### Parser Internals

`QueryMethodParser.parse(method_name)` returns a `ParsedQuery` dataclass:

```python
@dataclass
class ParsedQuery:
    prefix: str                          # "find_by", "count_by", "exists_by", "delete_by"
    predicates: list[FieldPredicate]     # [{field_name: "status", operator: "eq"}, ...]
    connectors: list[str]               # ["and", "or", ...]
    order_clauses: list[OrderClause]    # [{field_name: "name", direction: "desc"}, ...]
```

The parsing algorithm:
1. Extracts the prefix.
2. Splits off the `_order_by_` suffix.
3. Splits the remaining body by `_and_` and `_or_` connectors.
4. Parses each segment for field name and operator suffix (longest-match).

### Compiler Internals

`QueryMethodCompiler.compile(parsed, entity)` dispatches to the appropriate compile method based on the prefix and returns an async callable:

| Prefix       | Generated Query Pattern                             |
|--------------|-----------------------------------------------------|
| `find_by`    | `SELECT entity WHERE ... ORDER BY ...`              |
| `count_by`   | `SELECT COUNT(*) FROM entity WHERE ...`             |
| `exists_by`  | `SELECT COUNT(*) FROM entity WHERE ... > 0`         |
| `delete_by`  | `DELETE FROM entity WHERE ...` (returns `rowcount`) |

The compiler builds SQLAlchemy column expressions from each `FieldPredicate`, combines them using the connectors, and applies ORDER BY clauses from `OrderClause` objects.

---

## Complete CRUD Example

The following example demonstrates an entity, repository with derived queries, specifications, pagination, and mapping.

```python
# --- Entity ---

from pyfly.data.relational.sqlalchemy import BaseEntity
from sqlalchemy import String, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column


class Product(BaseEntity):
    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(255))
    price: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(100))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


# --- Repository ---

from pyfly.data.relational.sqlalchemy import Repository, query
from pyfly.container import repository as repo_stereotype
from sqlalchemy.ext.asyncio import AsyncSession


@repo_stereotype
class ProductRepository(Repository[Product, UUID]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Product, session)

    # Derived query methods (stubs, auto-compiled at startup)
    async def find_by_category(self, category: str) -> list[Product]: ...

    async def find_by_active_and_category(
        self, active: bool, category: str
    ) -> list[Product]: ...

    async def find_by_price_greater_than_order_by_price_desc(
        self, min_price: float
    ) -> list[Product]: ...

    async def find_by_name_containing(self, fragment: str) -> list[Product]: ...

    async def count_by_category(self, category: str) -> int: ...

    async def exists_by_name(self, name: str) -> bool: ...

    async def delete_by_active(self, active: bool) -> int: ...

    # Custom query method
    @query("SELECT p FROM Product p WHERE p.category = :category AND p.price > :min_price")
    async def find_expensive_in_category(
        self, category: str, min_price: float
    ) -> list[Product]: ...


# --- Service ---

from pyfly.container import service
from pyfly.data import Pageable, Sort, Page, Mapper
from pyfly.data.relational.sqlalchemy import FilterOperator, FilterUtils, Specification
from dataclasses import dataclass


@dataclass
class ProductDTO:
    id: str
    name: str
    price: float
    category: str


@service
class ProductService:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo
        self._mapper = Mapper()

    async def find_all_active(self, category: str | None = None) -> list[ProductDTO]:
        spec: Specification = FilterOperator.eq("active", True)
        if category:
            spec = spec & FilterOperator.eq("category", category)
        products = await self._repo.find_all_by_spec(spec)
        return self._mapper.map_list(products, ProductDTO)

    async def find_paginated(
        self,
        page: int = 1,
        size: int = 20,
        category: str | None = None,
    ) -> Page[ProductDTO]:
        spec = FilterOperator.eq("active", True)
        if category:
            spec = spec & FilterOperator.eq("category", category)

        pageable = Pageable.of(
            page=page,
            size=size,
            sort=Sort.by("name"),
        )

        result = await self._repo.find_all_by_spec_paged(spec, pageable)
        return result.map(lambda p: self._mapper.map(p, ProductDTO))

    async def search_by_name(self, query: str) -> list[ProductDTO]:
        products = await self._repo.find_by_name_containing(query)
        return self._mapper.map_list(products, ProductDTO)

    async def find_by_id(self, product_id: str) -> ProductDTO | None:
        from uuid import UUID
        product = await self._repo.find_by_id(UUID(product_id))
        if product is None:
            return None
        return self._mapper.map(product, ProductDTO)

    async def create(self, name: str, price: float, category: str) -> ProductDTO:
        product = Product(name=name, price=price, category=category)
        saved = await self._repo.save(product)
        return self._mapper.map(saved, ProductDTO)

    async def delete(self, product_id: str) -> None:
        from uuid import UUID
        await self._repo.delete(UUID(product_id))

    async def count_in_category(self, category: str) -> int:
        return await self._repo.count_by_category(category)
```

---

## Adapters

- [SQLAlchemy Adapter](../adapters/sqlalchemy.md) — Setup, configuration reference, and adapter-specific features for the SQLAlchemy backend
