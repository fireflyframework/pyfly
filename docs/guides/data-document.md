# MongoDB Data Access Guide

The PyFly MongoDB module provides a document-oriented data access layer built on Beanie ODM and Motor. It implements the same Repository pattern and derived query method convention as the relational (SQLAlchemy) adapter, sharing the framework-agnostic core -- `RepositoryPort`, `QueryMethodParser`, `Page`, `Pageable`, `Sort` -- while translating operations into native MongoDB queries. If you are coming from Spring Data MongoDB, the architecture will feel immediately familiar: PyFly Data is the commons layer, and the MongoDB adapter is a pluggable backend just like Spring Data MongoDB is to Spring Data Commons.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
  - [Spring Data Analogy](#spring-data-analogy)
  - [Layer Diagram](#layer-diagram)
  - [Imports](#imports)
- [Document Definition](#document-definition)
  - [BaseDocument](#basedocument)
  - [Audit Trail Fields](#audit-trail-fields)
  - [Settings Class](#settings-class)
  - [Indexed Fields](#indexed-fields)
  - [Defining Your Own Documents](#defining-your-own-documents)
- [MongoRepository\[T, ID\]](#mongorepositoryt-id)
  - [Creating a Repository](#creating-a-repository)
  - [CRUD Methods Reference](#crud-methods-reference)
  - [RepositoryPort Compliance](#repositoryport-compliance)
- [Derived Query Methods](#derived-query-methods)
  - [How It Works](#how-it-works)
  - [MongoQueryMethodCompiler Operator Mapping](#mongoquerymethodcompiler-operator-mapping)
  - [Connectors](#connectors)
  - [Ordering](#ordering)
  - [Complete Derived Query Examples](#complete-derived-query-examples)
- [Configuration](#configuration)
  - [DocumentProperties](#documentproperties)
  - [pyfly.yaml Keys](#pyflyyaml-keys)
  - [Environment Variables](#environment-variables)
- [Auto-Configuration](#auto-configuration)
  - [Detection Flow](#detection-flow)
  - [Beanie Initialization](#beanie-initialization)
  - [Document Class Discovery](#document-class-discovery)
- [Transaction Management](#transaction-management)
  - [mongo_transactional Decorator](#mongo_transactional-decorator)
  - [Replica Set Requirement](#replica-set-requirement)
  - [Usage Example](#usage-example)
- [MongoRepositoryBeanPostProcessor](#mongorepositorybeanbeanpostprocessor)
  - [How It Works](#how-it-works-1)
  - [Stub Detection](#stub-detection)
- [Pagination](#pagination)
  - [Paginated Queries](#paginated-queries)
  - [Sort Specification Building](#sort-specification-building)
  - [Page Result](#page-result)
- [Integration with Web Layer](#integration-with-web-layer)
  - [Controller with Valid\[T\] and MongoRepository](#controller-with-validt-and-mongorepository)
- [Complete CRUD Example](#complete-crud-example)
- [Architecture Extensibility](#architecture-extensibility)
  - [QueryMethodCompilerPort Protocol](#querymethodcompilerport-protocol)
  - [Adding a New Document Database Adapter](#adding-a-new-document-database-adapter)

---

## Architecture Overview

PyFly Data follows a layered, hexagonal architecture inspired by the Spring Data project family. Understanding these layers is key to using the MongoDB adapter effectively and appreciating how it relates to the rest of the data access infrastructure.

### Spring Data Analogy

PyFly Data maps directly to Spring Data's modular structure:

| Spring Data Module       | PyFly Equivalent                         | Purpose                                    |
|--------------------------|------------------------------------------|--------------------------------------------|
| Spring Data Commons      | `pyfly.data`                             | Shared ports, types, parser, `Page`, `Sort`|
| Spring Data JPA          | `pyfly.data.relational.sqlalchemy`         | Relational database adapter (SQLAlchemy)   |
| Spring Data MongoDB      | `pyfly.data.document.mongodb`            | Document database adapter (Beanie/Motor)   |

Both adapters build on the same framework-agnostic core. The `QueryMethodParser` lives in the commons layer and produces `ParsedQuery` objects. Each adapter provides its own `QueryMethodCompiler` implementation that translates those parsed queries into backend-specific operations -- SQLAlchemy column expressions for the relational adapter, or MongoDB filter documents for the document adapter.

### Layer Diagram

```
+----------------------------------------------------------------------+
|                          Your Application                            |
|  (Services, Controllers, Domain Logic)                               |
+----------------------------------------------------------------------+
          |                                        |
          v                                        v
+-----------------------------+    +-------------------------------+
|      pyfly.data (Commons)   |    |      pyfly.data (Commons)     |
|  RepositoryPort[T, ID]      |    |  RepositoryPort[T, ID]        |
|  Page, Pageable, Sort       |    |  Page, Pageable, Sort         |
|  QueryMethodParser          |    |  QueryMethodParser            |
|  QueryMethodCompilerPort    |    |  QueryMethodCompilerPort      |
+-----------------------------+    +-------------------------------+
          |                                        |
          v                                        v
+-----------------------------+    +-------------------------------+
| pyfly.data.relational       |    | pyfly.data.document           |
|        .sqlalchemy          |    |        .mongodb               |
|                             |    |                               |
| Repository[T, ID]           |    | MongoRepository[T, ID]        |
| BaseEntity                  |    | BaseDocument                  |
| QueryMethodCompiler         |    | MongoQueryMethodCompiler      |
| RepositoryBeanPostProcessor |    | MongoRepositoryBeanPostProc.  |
| reactive_transactional      |    | mongo_transactional           |
+-----------------------------+    +-------------------------------+
          |                                        |
          v                                        v
+-----------------------------+    +-------------------------------+
|     SQLAlchemy (async)      |    |  Beanie ODM  +  Motor (async) |
|     PostgreSQL / MySQL /    |    |  MongoDB                      |
|     SQLite / etc.           |    |                               |
+-----------------------------+    +-------------------------------+
```

The left column is the relational path (covered in the [Data Access Guide](./data-relational.md)). The right column is the document path covered in this guide. Both paths share the top commons layer, so concepts like `Page`, `Pageable`, `Sort`, derived query naming conventions, and the `RepositoryPort` protocol are identical.

### Imports

The MongoDB adapter is accessible from the `pyfly.data.document` package:

```python
from pyfly.data.document import (
    # Framework-agnostic (shared with SQLAlchemy adapter)
    Page, Pageable, Sort, Order, Mapper,
    RepositoryPort, QueryMethodParser, QueryMethodCompilerPort,
    # MongoDB adapter
    BaseDocument, MongoRepository,
    MongoQueryMethodCompiler, MongoRepositoryBeanPostProcessor,
    mongo_transactional,
)
```

You can also import directly from the adapter package:

```python
from pyfly.data.document.mongodb import (
    BaseDocument,
    MongoRepository,
    MongoQueryMethodCompiler,
    MongoRepositoryBeanPostProcessor,
    initialize_beanie,
    mongo_transactional,
)
```

Source files:
- `src/pyfly/data/document/__init__.py` -- document sub-layer re-exports
- `src/pyfly/data/document/mongodb/__init__.py` -- MongoDB adapter package exports

---

## Document Definition

### BaseDocument

`BaseDocument` is the base class for all MongoDB documents in a PyFly application. It extends `beanie.Document` and provides audit trail fields that are automatically populated on insert and update.

```python
from pyfly.data.document.mongodb import BaseDocument
```

All domain documents should inherit from `BaseDocument` to gain the automatic audit trail, just as all relational entities inherit from `BaseEntity` in the SQLAlchemy adapter.

### Audit Trail Fields

`BaseDocument` provides four audit trail fields in addition to the `id` field inherited from `beanie.Document`:

| Field        | Type              | Default                         | Description                          |
|--------------|-------------------|---------------------------------|--------------------------------------|
| `id`         | `PydanticObjectId`| Auto-generated by MongoDB       | Document primary key (ObjectId)      |
| `created_at` | `datetime`        | `datetime.now(UTC)` on creation | Timestamp when the document was created |
| `updated_at` | `datetime`        | `datetime.now(UTC)` on creation | Timestamp of the last update         |
| `created_by` | `str \| None`     | `None`                          | Creator identifier                   |
| `updated_by` | `str \| None`     | `None`                          | Last updater identifier              |

The `created_at` and `updated_at` fields use `pydantic.Field(default_factory=...)` with a lambda that calls `datetime.now(UTC)`, ensuring timezone-aware UTC timestamps.

The `BaseDocument` class also enables Beanie state management:

```python
class BaseDocument(Document):
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_by: str | None = None
    updated_by: str | None = None

    class Settings:
        use_state_management = True
```

With `use_state_management = True`, Beanie tracks which fields have changed since the document was loaded, enabling efficient partial updates via `save_changes()`.

### Settings Class

Every Beanie document uses an inner `Settings` class to configure collection-level options. The most important setting is `name`, which defines the MongoDB collection name:

```python
class UserDocument(BaseDocument):
    name: str
    email: str

    class Settings:
        name = "users"
```

If you omit the `Settings` class or the `name` attribute, Beanie derives the collection name from the class name (e.g., `UserDocument` becomes `UserDocument` as the collection name). It is best practice to always set `name` explicitly for clarity and consistency.

Common `Settings` attributes:

| Attribute              | Type   | Description                                           |
|------------------------|--------|-------------------------------------------------------|
| `name`                 | `str`  | MongoDB collection name                               |
| `use_state_management` | `bool` | Track field changes for partial updates (inherited from `BaseDocument`) |
| `indexes`              | `list` | Additional Beanie index definitions                   |

### Indexed Fields

You can define indexes using Beanie's `Indexed` type or the `Settings.indexes` list. The `Indexed` type is the simplest approach for single-field indexes:

```python
from beanie import Indexed

class UserDocument(BaseDocument):
    name: str
    email: Indexed(str, unique=True)
    role: Indexed(str)

    class Settings:
        name = "users"
```

For compound indexes or more complex index configurations, use the `Settings.indexes` list:

```python
from pymongo import IndexModel, ASCENDING, DESCENDING

class OrderDocument(BaseDocument):
    customer_id: str
    status: str
    total: float
    region: str

    class Settings:
        name = "orders"
        indexes = [
            IndexModel(
                [("customer_id", ASCENDING), ("status", ASCENDING)],
                name="idx_customer_status",
            ),
            IndexModel(
                [("region", ASCENDING), ("total", DESCENDING)],
                name="idx_region_total",
            ),
        ]
```

Indexes are created automatically when Beanie initializes the document models during application startup.

### Defining Your Own Documents

Extend `BaseDocument` and declare your domain fields using standard Pydantic field declarations:

```python
from pyfly.data.document.mongodb import BaseDocument
from beanie import Indexed
from pydantic import Field


class ProductDocument(BaseDocument):
    name: str
    sku: Indexed(str, unique=True)
    description: str = ""
    price: float = Field(gt=0)
    category: str
    tags: list[str] = Field(default_factory=list)
    active: bool = True

    class Settings:
        name = "products"
```

This document will have all five inherited fields (`id`, `created_at`, `updated_at`, `created_by`, `updated_by`) plus your seven custom fields. Because `BaseDocument` extends `beanie.Document` (which extends `pydantic.BaseModel`), all Pydantic validation, serialization, and field configuration features are available.

Nested documents use standard Pydantic models:

```python
from pydantic import BaseModel


class Address(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str


class CustomerDocument(BaseDocument):
    name: str
    email: str
    address: Address | None = None
    tags: list[str] = Field(default_factory=list)

    class Settings:
        name = "customers"
```

Source file: `src/pyfly/data/document/mongodb/document.py`

---

## MongoRepository[T, ID]

The `MongoRepository[T, ID]` class provides generic async CRUD operations for Beanie documents. It mirrors the `Repository[T, ID]` class from the SQLAlchemy adapter but operates against MongoDB. The two type parameters are:

- **T** -- The document type (a `BaseDocument` subclass)
- **ID** -- The primary key type (typically `PydanticObjectId` or `str`)

Unlike the SQLAlchemy `Repository`, `MongoRepository` does not require a session to be injected. Beanie uses a globally initialized Motor client, so the repository only needs the document model class:

```python
from pyfly.data.document.mongodb import MongoRepository, BaseDocument

repo = MongoRepository[ProductDocument, str](ProductDocument)
product = await repo.save(ProductDocument(name="Widget", price=9.99, category="gadgets"))
found = await repo.find_by_id(product.id)
```

### Creating a Repository

Subclass `MongoRepository[T, ID]` and register it as a bean with the `@repository` stereotype:

```python
from pyfly.data.document.mongodb import MongoRepository
from pyfly.container import repository as repo_stereotype


@repo_stereotype
class ProductRepository(MongoRepository[ProductDocument, str]):
    def __init__(self) -> None:
        super().__init__(ProductDocument)
```

Notice that unlike the SQLAlchemy `Repository`, the constructor does not accept a session parameter. Beanie handles the database connection globally through the Motor client initialized at startup.

For documents with `PydanticObjectId` primary keys (the default):

```python
from beanie import PydanticObjectId


@repo_stereotype
class OrderRepository(MongoRepository[OrderDocument, PydanticObjectId]):
    def __init__(self) -> None:
        super().__init__(OrderDocument)
```

### CRUD Methods Reference

| Method                                     | Return Type  | Description                                    |
|--------------------------------------------|--------------|------------------------------------------------|
| `save(entity)`                             | `T`          | Insert or update; calls `entity.save()`        |
| `find_by_id(id: ID)`                       | `T \| None`  | Find by primary key via `model.get(id)`        |
| `find_all(**filters)`                       | `list[T]`    | Find all, optionally filtered by field values  |
| `delete(id: ID)`                            | `None`       | Delete by primary key (no-op if not found)     |
| `count()`                                   | `int`        | Count all documents in the collection          |
| `exists(id: ID)`                            | `bool`       | Check if a document with this ID exists        |
| `find_paginated(page, size, pageable)`      | `Page[T]`    | Paginated query with optional sorting          |

**save()** calls Beanie's `entity.save()`, which performs an upsert -- inserting the document if it is new or updating it if it already exists. The returned entity is the same object with any server-side defaults applied.

**find_all()** accepts keyword arguments that are translated into equality filters passed to Beanie's `find()`:

```python
orders = await repo.find_all(status="PENDING", customer_id="abc")
# Equivalent to: db.orders.find({"status": "PENDING", "customer_id": "abc"})
```

When called without filters, it returns all documents in the collection.

**delete()** looks up the entity by ID first, then calls `entity.delete()` if found. If not found, it is a no-op.

**find_paginated()** supports both simple page/size arguments and a `Pageable` object:

```python
# Simple pagination
page = await repo.find_paginated(page=1, size=20)

# With Pageable and sorting
from pyfly.data import Pageable, Sort

pageable = Pageable.of(page=1, size=20, sort=Sort.by("name"))
page = await repo.find_paginated(pageable=pageable)
```

### RepositoryPort Compliance

`MongoRepository` satisfies the `RepositoryPort[T, ID]` protocol defined in `pyfly.data.ports.outbound`. This means your service layer can depend on `RepositoryPort` rather than the concrete `MongoRepository`, enabling clean hexagonal architecture:

```python
from pyfly.data import RepositoryPort


class ProductService:
    def __init__(self, repo: RepositoryPort[ProductDocument, str]) -> None:
        self._repo = repo

    async def find_active(self) -> list[ProductDocument]:
        return await self._repo.find_all(active=True)
```

The `RepositoryPort` protocol defines the same core CRUD methods that `MongoRepository` implements:

```python
class RepositoryPort(Protocol[T, ID]):
    async def save(self, entity: T) -> T: ...
    async def find_by_id(self, id: ID) -> T | None: ...
    async def find_all(self, **filters: Any) -> list[T]: ...
    async def delete(self, id: ID) -> None: ...
    async def count(self) -> int: ...
    async def exists(self, id: ID) -> bool: ...
```

This shared interface allows you to swap between the SQLAlchemy and MongoDB adapters without changing service layer code, as long as the entity/document types align.

Source file: `src/pyfly/data/document/mongodb/repository.py`

---

## Derived Query Methods

PyFly can automatically generate MongoDB query implementations from method names, following the same Spring Data naming convention used by the SQLAlchemy adapter. You define stub methods on your repository, and the `MongoRepositoryBeanPostProcessor` compiles them into real MongoDB queries at startup.

### How It Works

The derived query pipeline consists of two stages, split between the shared commons layer and the MongoDB adapter:

1. **Parsing (shared):** The `QueryMethodParser` (from `pyfly.data.query_parser`) parses the method name into a `ParsedQuery` containing predicates, connectors, and order clauses. This parser is identical for both the SQLAlchemy and MongoDB adapters.

2. **Compilation (adapter-specific):** The `MongoQueryMethodCompiler` (from `pyfly.data.document.mongodb.query_compiler`) takes the `ParsedQuery` and compiles it into an async callable that builds a MongoDB filter document and executes it via Beanie.

Because the parser is shared, the naming convention is identical to the one documented in the [Data Access Guide](./data-relational.md). The prefixes, operators, connectors, and ordering suffixes are the same -- only the compiled output differs.

### MongoQueryMethodCompiler Operator Mapping

The `MongoQueryMethodCompiler._build_clause()` method translates each parsed operator into a MongoDB filter expression. The following table shows the complete mapping:

| Operator       | Method Suffix          | MongoDB Filter Expression                    | Args |
|----------------|------------------------|----------------------------------------------|------|
| `eq`           | *(none)*               | `{field: value}`                             | 1    |
| `not`          | `_not`                 | `{field: {"$ne": value}}`                    | 1    |
| `gt`           | `_greater_than`        | `{field: {"$gt": value}}`                    | 1    |
| `gte`          | `_greater_than_equal`  | `{field: {"$gte": value}}`                   | 1    |
| `lt`           | `_less_than`           | `{field: {"$lt": value}}`                    | 1    |
| `lte`          | `_less_than_equal`     | `{field: {"$lte": value}}`                   | 1    |
| `between`      | `_between`             | `{field: {"$gte": low, "$lte": high}}`       | 2    |
| `like`         | `_like`                | `{field: {"$regex": pattern}}`               | 1    |
| `containing`   | `_containing`          | `{field: {"$regex": ".*value.*", "$options": "i"}}` | 1 |
| `in`           | `_in`                  | `{field: {"$in": values}}`                   | 1 (list) |
| `is_null`      | `_is_null`             | `{field: None}`                              | 0    |
| `is_not_null`  | `_is_not_null`         | `{field: {"$ne": None}}`                     | 0    |

Key notes on the MongoDB-specific behavior:

- **`containing`** uses a case-insensitive regex (`$options: "i"`) and wraps the value in `.*...*`. The value is regex-escaped to prevent injection.
- **`like`** translates SQL LIKE syntax: `%` becomes `.*` and `_` becomes `.` in the regex pattern. The rest of the value is regex-escaped.
- **`between`** consumes two arguments and combines them into a single filter with both `$gte` and `$lte`.
- **`is_null`** and **`is_not_null`** consume zero arguments.

### Connectors

Multiple predicates are connected with `_and_` or `_or_`, producing MongoDB's `$and` or `$or` operators:

```python
# AND: {"$and": [{"status": "ACTIVE"}, {"role": "admin"}]}
async def find_by_status_and_role(self, status: str, role: str) -> list[UserDocument]: ...

# OR: {"$or": [{"status": "ACTIVE"}, {"role": "admin"}]}
async def find_by_status_or_role(self, status: str, role: str) -> list[UserDocument]: ...
```

When all connectors are the same type, the compiler produces a flat `$and` or `$or` array. When connectors are mixed (both AND and OR in one method name), the compiler builds a nested expression evaluated left to right:

```python
# Mixed: find where status=? AND (role=? OR active=?)
# This is built as: {"$and": [{"$and": [{"status": ?}, {"role": ?}]}, {"active": ?}]}
async def find_by_status_and_role_or_active(
    self, status: str, role: str, active: bool
) -> list[UserDocument]: ...
```

For a single predicate with no connectors, the filter is a plain document (no `$and` wrapper):

```python
# Simple: {"email": value}
async def find_by_email(self, email: str) -> list[UserDocument]: ...
```

### Ordering

Append `_order_by_{field}_{asc|desc}` to control result ordering. The compiler translates these into pymongo sort specifications:

```python
# Sort by created_at descending: [("created_at", pymongo.DESCENDING)]
async def find_by_status_order_by_created_at_desc(
    self, status: str
) -> list[OrderDocument]: ...

# Multiple sort fields: [("name", ASCENDING), ("created_at", DESCENDING)]
async def find_by_active_order_by_name_asc_created_at_desc(
    self, active: bool
) -> list[UserDocument]: ...
```

### Complete Derived Query Examples

```python
@repo_stereotype
class OrderRepository(MongoRepository[OrderDocument, PydanticObjectId]):
    def __init__(self) -> None:
        super().__init__(OrderDocument)

    # Equals (default operator)
    # -> {"status": value}
    async def find_by_status(self, status: str) -> list[OrderDocument]: ...

    # Multiple conditions with AND
    # -> {"$and": [{"customer_id": value}, {"status": value}]}
    async def find_by_customer_id_and_status(
        self, customer_id: str, status: str
    ) -> list[OrderDocument]: ...

    # Greater than
    # -> {"total": {"$gt": value}}
    async def find_by_total_greater_than(self, min_total: float) -> list[OrderDocument]: ...

    # Between (takes 2 arguments)
    # -> {"total": {"$gte": low, "$lte": high}}
    async def find_by_total_between(self, low: float, high: float) -> list[OrderDocument]: ...

    # Contains (case-insensitive regex)
    # -> {"customer_id": {"$regex": ".*value.*", "$options": "i"}}
    async def find_by_customer_id_containing(self, fragment: str) -> list[OrderDocument]: ...

    # IN a list
    # -> {"status": {"$in": ["PENDING", "SHIPPED"]}}
    async def find_by_status_in(self, statuses: list[str]) -> list[OrderDocument]: ...

    # IS NULL (zero arguments consumed)
    # -> {"deleted_at": None}
    async def find_by_deleted_at_is_null(self) -> list[OrderDocument]: ...

    # IS NOT NULL
    # -> {"email": {"$ne": None}}
    async def find_by_email_is_not_null(self) -> list[OrderDocument]: ...

    # COUNT prefix
    # -> count({role: value})
    async def count_by_role(self, role: str) -> int: ...

    # EXISTS prefix
    # -> count({email: value}) > 0
    async def exists_by_email(self, email: str) -> bool: ...

    # DELETE prefix (returns number of deleted documents)
    # -> finds all matching, deletes each, returns count
    async def delete_by_status(self, status: str) -> int: ...

    # With ordering
    # -> find({"status": value}).sort([("created_at", DESCENDING)])
    async def find_by_status_order_by_created_at_desc(
        self, status: str
    ) -> list[OrderDocument]: ...

    # Complex: AND + ordering
    # -> find({"$and": [{status: ?}, {customer_id: ?}]}).sort([("total", DESCENDING)])
    async def find_by_status_and_customer_id_order_by_total_desc(
        self, status: str, customer_id: str
    ) -> list[OrderDocument]: ...
```

Each method body should be a stub (`...` or `pass`). The `MongoRepositoryBeanPostProcessor` detects them and replaces them with real implementations at startup.

Source file: `src/pyfly/data/document/mongodb/query_compiler.py`

---

## Configuration

### DocumentProperties

The `DocumentProperties` dataclass captures all document database configuration under the `pyfly.data.document.*` namespace:

```python
from pyfly.core.config import config_properties
from dataclasses import dataclass


@config_properties(prefix="pyfly.data.document")
@dataclass
class DocumentProperties:
    enabled: bool = False
    uri: str = "mongodb://localhost:27017"
    database: str = "pyfly"
    min_pool_size: int = 0
    max_pool_size: int = 100
```

| Field           | Type   | Default                      | Description                                      |
|-----------------|--------|------------------------------|--------------------------------------------------|
| `enabled`       | `bool` | `False`                      | Enable the MongoDB subsystem                     |
| `uri`           | `str`  | `"mongodb://localhost:27017"`| MongoDB connection URI                           |
| `database`      | `str`  | `"pyfly"`                    | Database name to connect to                      |
| `min_pool_size` | `int`  | `0`                          | Minimum number of connections in the Motor pool  |
| `max_pool_size` | `int`  | `100`                        | Maximum number of connections in the Motor pool  |

### pyfly.yaml Keys

Configure MongoDB in your `pyfly.yaml` (or `application.yml`):

```yaml
pyfly:
  data:
    document:
      enabled: true
      uri: mongodb://localhost:27017
      database: my_app
      min_pool_size: 5
      max_pool_size: 50
```

For a MongoDB Atlas connection:

```yaml
pyfly:
  data:
    document:
      enabled: true
      uri: mongodb+srv://user:password@cluster.mongodb.net/?retryWrites=true&w=majority
      database: production_db
      min_pool_size: 10
      max_pool_size: 100
```

For a replica set deployment (required for transactions):

```yaml
pyfly:
  data:
    document:
      enabled: true
      uri: mongodb://mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs0
      database: my_app
      min_pool_size: 5
      max_pool_size: 50
```

### Environment Variables

Following PyFly's configuration resolution order, you can override any MongoDB property with environment variables. The pattern is the YAML key path with dots replaced by underscores and uppercased:

| Environment Variable       | Overrides                   | Example                          |
|----------------------------|-----------------------------|----------------------------------|
| `PYFLY_DATA_DOCUMENT_ENABLED`   | `pyfly.data.document.enabled`    | `true`                           |
| `PYFLY_DATA_DOCUMENT_URI`       | `pyfly.data.document.uri`        | `mongodb://prod-host:27017`      |
| `PYFLY_DATA_DOCUMENT_DATABASE`  | `pyfly.data.document.database`   | `production_db`                  |
| `PYFLY_DATA_DOCUMENT_MIN_POOL_SIZE` | `pyfly.data.document.min_pool_size` | `10`                       |
| `PYFLY_DATA_DOCUMENT_MAX_POOL_SIZE` | `pyfly.data.document.max_pool_size` | `200`                      |

This is useful for containerized deployments where secrets and connection strings are injected via environment:

```bash
export PYFLY_DATA_DOCUMENT_ENABLED=true
export PYFLY_DATA_DOCUMENT_URI="mongodb+srv://user:secret@cluster.mongodb.net"
export PYFLY_DATA_DOCUMENT_DATABASE=production_db
```

Source file: `src/pyfly/config/properties/mongodb.py` (class `DocumentProperties`)

---

## Auto-Configuration

PyFly uses a config-driven auto-configuration system to detect and wire the MongoDB adapter at startup. This mirrors the Spring Boot auto-configuration pattern.

### Detection Flow

The `AutoConfigurationEngine` processes the MongoDB subsystem in its `_configure_document()` method. The flow is:

1. **Check enabled flag.** Read `pyfly.data.document.enabled` from config. If `false` (the default), the MongoDB subsystem is skipped entirely.

2. **Detect provider.** Call `AutoConfiguration.detect_document_provider()`, which checks whether the `beanie` package is importable. If it is, the provider is `"beanie"`. If not, the provider is `"none"` and MongoDB is skipped.

3. **Read connection settings.** Extract `pyfly.data.document.uri` and `pyfly.data.document.database` from config.

4. **Register results.** Store the provider name and connection configuration for use during application startup.

```python
class AutoConfiguration:
    @staticmethod
    def detect_document_provider() -> str:
        """Detect the best available MongoDB / document DB provider."""
        if AutoConfiguration.is_available("beanie"):
            return "beanie"
        return "none"
```

The detection is purely library-based: if Beanie is installed in your Python environment, the MongoDB adapter is available. You still need to set `pyfly.data.document.enabled: true` in config to activate it.

```python
def _configure_document(self, config: Config, container: Container) -> None:
    """Auto-configure MongoDB layer if enabled."""
    enabled = config.get("pyfly.data.document.enabled", False)
    if not _as_bool(enabled):
        logger.info("auto_configuration", subsystem="mongodb", status="skipped", reason="disabled")
        return

    provider = AutoConfiguration.detect_document_provider()
    if provider == "none":
        logger.info("auto_configuration", subsystem="mongodb", status="skipped", reason="no provider")
        return

    uri = str(config.get("pyfly.data.document.uri", "mongodb://localhost:27017"))
    database = str(config.get("pyfly.data.document.database", "pyfly"))

    self._results["mongodb"] = provider
    self._document_config = {"uri": uri, "database": database}
    logger.info(
        "auto_configuration",
        subsystem="mongodb",
        status="configured",
        provider=provider,
        database=database,
    )
```

### Beanie Initialization

Beanie requires explicit initialization before any document operations can be performed. The `initialize_beanie()` helper function in the MongoDB adapter handles this:

```python
from pyfly.data.document.mongodb import initialize_beanie


client = await initialize_beanie(
    uri="mongodb://localhost:27017",
    database="my_app",
    document_models=[ProductDocument, OrderDocument, CustomerDocument],
)
```

This function:
1. Creates an `AsyncIOMotorClient` with the provided URI.
2. Selects the target database from the client.
3. Calls Beanie's `init_beanie()` with the database and document model list.
4. Returns the Motor client instance for lifecycle management (e.g., closing on shutdown).

```python
async def initialize_beanie(
    uri: str,
    database: str,
    document_models: list[type],
) -> AsyncIOMotorClient:
    client: AsyncIOMotorClient = AsyncIOMotorClient(uri)
    await init_beanie(database=client[database], document_models=document_models)
    return client
```

Typically, you call `initialize_beanie()` during your application's startup phase (e.g., in a lifespan handler or `@pyfly_application` startup hook).

### Document Class Discovery

For the `document_models` parameter, you need to provide all Beanie `Document` subclasses that your application uses. A typical pattern is to collect them in a central module:

```python
# documents/__init__.py
from documents.product import ProductDocument
from documents.order import OrderDocument
from documents.customer import CustomerDocument

ALL_DOCUMENTS = [ProductDocument, OrderDocument, CustomerDocument]
```

Then pass them during initialization:

```python
from documents import ALL_DOCUMENTS
from pyfly.data.document.mongodb import initialize_beanie


async def startup():
    client = await initialize_beanie(
        uri="mongodb://localhost:27017",
        database="my_app",
        document_models=ALL_DOCUMENTS,
    )
```

Source files:
- `src/pyfly/config/auto.py` -- `AutoConfiguration`, `AutoConfigurationEngine._configure_document()`
- `src/pyfly/data/document/mongodb/initializer.py` -- `initialize_beanie()`

---

## Transaction Management

### mongo_transactional Decorator

The `@mongo_transactional` decorator provides declarative async transaction management for MongoDB, mirroring the `@reactive_transactional` decorator from the SQLAlchemy adapter:

```python
from pyfly.data.document.mongodb import mongo_transactional
from motor.motor_asyncio import AsyncIOMotorClient

client: AsyncIOMotorClient = ...


@mongo_transactional(client)
async def transfer_funds(from_id: str, to_id: str, amount: float) -> None:
    from_account = await AccountDocument.get(from_id)
    to_account = await AccountDocument.get(to_id)

    from_account.balance -= amount
    to_account.balance += amount

    await from_account.save()
    await to_account.save()
    # Transaction is committed automatically on success
    # Transaction is aborted automatically on exception
```

**How it works:**

1. Starts a new Motor session via `client.start_session()`.
2. Begins a transaction on the session via `session.start_transaction()`.
3. Calls the wrapped function with all original arguments.
4. On success: the transaction is committed (via the `async with` context manager).
5. On exception: the transaction is aborted and the exception is re-raised.

```python
def mongo_transactional(client: AsyncIOMotorClient) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            async with await client.start_session() as session:
                async with session.start_transaction():
                    result = await func(*args, **kwargs)
                    return result
        return wrapper
    return decorator
```

Unlike `@reactive_transactional` (which injects the session as the first argument), `@mongo_transactional` does not inject the session. The Beanie document operations automatically participate in the active transaction through Motor's session context.

### Replica Set Requirement

MongoDB transactions require a replica set deployment. Standalone MongoDB instances do not support multi-document transactions. If you attempt to use `@mongo_transactional` against a standalone instance, MongoDB will raise an error.

For local development, you can run a single-node replica set:

```bash
# Start MongoDB as a single-node replica set
mongod --replSet rs0 --bind_ip localhost --port 27017

# Initialize the replica set (run once in mongosh)
rs.initiate({_id: "rs0", members: [{_id: 0, host: "localhost:27017"}]})
```

Or use Docker Compose:

```yaml
version: "3.8"
services:
  mongo:
    image: mongo:7
    command: ["--replSet", "rs0", "--bind_ip_all"]
    ports:
      - "27017:27017"
    healthcheck:
      test: |
        mongosh --eval 'try { rs.status() } catch { rs.initiate({_id:"rs0",members:[{_id:0,host:"localhost:27017"}]}) }'
      interval: 10s
      start_period: 30s
```

### Usage Example

A complete example showing transactional order processing:

```python
from pyfly.data.document.mongodb import mongo_transactional, initialize_beanie

# Initialize Beanie during startup
client = await initialize_beanie(
    uri="mongodb://localhost:27017/?replicaSet=rs0",
    database="my_app",
    document_models=[OrderDocument, InventoryDocument],
)


@mongo_transactional(client)
async def place_order(customer_id: str, product_id: str, quantity: int) -> OrderDocument:
    """Place an order and decrement inventory atomically."""
    # Decrement inventory
    inventory = await InventoryDocument.find_one(
        InventoryDocument.product_id == product_id
    )
    if inventory is None or inventory.quantity < quantity:
        raise ValueError("Insufficient inventory")

    inventory.quantity -= quantity
    await inventory.save()

    # Create order
    order = OrderDocument(
        customer_id=customer_id,
        product_id=product_id,
        quantity=quantity,
        status="CONFIRMED",
    )
    await order.save()
    return order
    # Both operations commit together, or both are rolled back
```

Source file: `src/pyfly/data/document/mongodb/transactional.py`

---

## MongoRepositoryBeanPostProcessor

The `MongoRepositoryBeanPostProcessor` is a `BeanPostProcessor` that runs after each repository bean is initialized. It scans the repository class for stub methods and replaces them with real MongoDB query implementations. It mirrors the `RepositoryBeanPostProcessor` from the SQLAlchemy adapter but targets MongoDB via Beanie ODM.

### How It Works

The `after_init(bean, bean_name)` method:

1. **Checks the bean type.** If the bean is not an instance of `MongoRepository`, it is returned unchanged.

2. **Identifies custom methods.** Iterates over all attributes defined on the bean's class (excluding private attributes starting with `_` and methods inherited from the base `MongoRepository`).

3. **Detects derived query methods.** For each method that starts with a recognized prefix (`find_by_`, `count_by_`, `exists_by_`, `delete_by_`) and is a stub, the processor:
   - Parses the method name via `QueryMethodParser.parse()`.
   - Compiles the parsed query via `MongoQueryMethodCompiler.compile()`.
   - Wraps the compiled function to inject `bean._model`.
   - Replaces the stub method on the bean instance.

```python
class MongoRepositoryBeanPostProcessor:
    def __init__(self) -> None:
        self._query_parser = QueryMethodParser()
        self._query_compiler = MongoQueryMethodCompiler()

    def after_init(self, bean: Any, bean_name: str) -> Any:
        if not isinstance(bean, MongoRepository):
            return bean

        cls = type(bean)
        base_names = set(dir(MongoRepository))

        for attr_name in list(vars(cls)):
            if attr_name.startswith("_"):
                continue

            attr = getattr(cls, attr_name, None)
            if attr is None or not callable(attr):
                continue

            if attr_name in base_names:
                continue

            if any(attr_name.startswith(prefix) for prefix in _DERIVED_PREFIXES) and self._is_stub(attr):
                parsed = self._query_parser.parse(attr_name)
                compiled_fn = self._query_compiler.compile(parsed, bean._model)
                wrapper = self._wrap_derived_method(compiled_fn)
                setattr(bean, attr_name, wrapper.__get__(bean, cls))

        return bean
```

The wrapper function injects `bean._model` as the first argument to the compiled query function:

```python
@staticmethod
def _wrap_derived_method(compiled_fn: Any) -> Any:
    async def wrapper(self_arg: Any, *args: Any) -> Any:
        return await compiled_fn(self_arg._model, *args)
    return wrapper
```

### Stub Detection

A method is considered a stub when its code object contains no meaningful constants beyond `None` and `Ellipsis`. This covers both forms:

```python
async def find_by_status(self, status: str) -> list[OrderDocument]: ...    # Ellipsis stub
async def find_by_status(self, status: str) -> list[OrderDocument]: pass   # Pass stub
```

The detection logic:

```python
@staticmethod
def _is_stub(method: Any) -> bool:
    func = method
    if isinstance(func, (staticmethod, classmethod)):
        func = func.__func__
    if hasattr(func, "__wrapped__"):
        func = func.__wrapped__

    code = getattr(func, "__code__", None)
    if code is None:
        return False

    consts = set(code.co_consts)
    consts.discard(None)
    consts.discard(Ellipsis)

    return len(consts) == 0 and code.co_code is not None
```

Register the post-processor in your application context:

```python
from pyfly.data.document.mongodb import MongoRepositoryBeanPostProcessor

context.register_post_processor(MongoRepositoryBeanPostProcessor())
```

Source file: `src/pyfly/data/document/mongodb/post_processor.py`

---

## Pagination

### Paginated Queries

The `find_paginated()` method on `MongoRepository` supports both simple page/size arguments and a full `Pageable` object with sorting:

```python
# Basic pagination (page 1, 20 items per page)
page = await repo.find_paginated(page=1, size=20)

# With Pageable (overrides page/size and adds sorting)
from pyfly.data import Pageable, Sort

pageable = Pageable.of(
    page=2,
    size=10,
    sort=Sort.by("created_at").descending(),
)
page = await repo.find_paginated(pageable=pageable)
```

When a `pageable` is provided, its `page`, `size`, and `sort` override the primitive `page` and `size` arguments.

The implementation:
1. Counts total documents in the collection via `find_all().count()`.
2. Calculates the offset: `(page - 1) * size`.
3. Builds a sort specification from the `Pageable.sort` orders (if provided).
4. Applies `.sort()`, `.skip()`, and `.limit()` to the Beanie query.
5. Returns a `Page[T]` with the items, total count, page number, and size.

### Sort Specification Building

The `_build_sort()` static method translates a `Pageable`'s `Sort` orders into pymongo sort tuples:

```python
@staticmethod
def _build_sort(pageable: Pageable) -> list[tuple[str, int]]:
    sort_spec: list[tuple[str, int]] = []
    for order in pageable.sort.orders:
        direction = pymongo.ASCENDING if order.direction == "asc" else pymongo.DESCENDING
        sort_spec.append((order.property, direction))
    return sort_spec
```

For example, `Sort(orders=(Order.desc("created_at"), Order.asc("name")))` becomes:

```python
[("created_at", pymongo.DESCENDING), ("name", pymongo.ASCENDING)]
```

### Page Result

`find_paginated()` returns a `Page[T]` -- the same `Page` dataclass used by the SQLAlchemy adapter:

```python
page = await repo.find_paginated(page=1, size=20)

page.items          # list[ProductDocument] -- the items on this page
page.total          # int -- total items across all pages
page.page           # int -- current page number (1-based)
page.size           # int -- maximum items per page
page.total_pages    # int -- total number of pages (ceil(total / size))
page.has_next       # bool -- whether there is a next page
page.has_previous   # bool -- whether there is a previous page
```

Transform items with the `map()` method:

```python
from pydantic import BaseModel


class ProductDTO(BaseModel):
    id: str
    name: str
    price: float


dto_page: Page[ProductDTO] = page.map(
    lambda doc: ProductDTO(id=str(doc.id), name=doc.name, price=doc.price)
)
```

---

## Integration with Web Layer

### Controller with Valid[T] and MongoRepository

The MongoDB adapter integrates seamlessly with PyFly's web layer. Here is a complete example showing a controller that uses `Valid[T]` for request validation and a `MongoRepository` for data access:

```python
# --- Document ---

from pyfly.data.document.mongodb import BaseDocument
from beanie import Indexed
from pydantic import Field


class TaskDocument(BaseDocument):
    title: str
    description: str = ""
    priority: Indexed(int) = 0
    status: str = "TODO"
    assignee: str | None = None

    class Settings:
        name = "tasks"


# --- Repository ---

from pyfly.data.document.mongodb import MongoRepository
from pyfly.container import repository as repo_stereotype


@repo_stereotype
class TaskRepository(MongoRepository[TaskDocument, str]):
    def __init__(self) -> None:
        super().__init__(TaskDocument)

    async def find_by_status(self, status: str) -> list[TaskDocument]: ...

    async def find_by_assignee_and_status(
        self, assignee: str, status: str
    ) -> list[TaskDocument]: ...

    async def find_by_priority_greater_than_order_by_priority_desc(
        self, min_priority: int
    ) -> list[TaskDocument]: ...

    async def count_by_status(self, status: str) -> int: ...


# --- Request/Response Models ---

from pydantic import BaseModel


class CreateTaskRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str = ""
    priority: int = Field(0, ge=0, le=10)
    assignee: str | None = None


class TaskResponse(BaseModel):
    id: str
    title: str
    description: str
    priority: int
    status: str
    assignee: str | None


# --- Service ---

from pyfly.container import service
from pyfly.data import Mapper


@service
class TaskService:
    def __init__(self, repo: TaskRepository) -> None:
        self._repo = repo
        self._mapper = Mapper()

    async def create(self, request: CreateTaskRequest) -> TaskResponse:
        doc = TaskDocument(
            title=request.title,
            description=request.description,
            priority=request.priority,
            assignee=request.assignee,
        )
        saved = await self._repo.save(doc)
        return TaskResponse(
            id=str(saved.id),
            title=saved.title,
            description=saved.description,
            priority=saved.priority,
            status=saved.status,
            assignee=saved.assignee,
        )

    async def find_by_id(self, task_id: str) -> TaskResponse | None:
        doc = await self._repo.find_by_id(task_id)
        if doc is None:
            return None
        return TaskResponse(
            id=str(doc.id),
            title=doc.title,
            description=doc.description,
            priority=doc.priority,
            status=doc.status,
            assignee=doc.assignee,
        )

    async def find_by_status(self, status: str) -> list[TaskResponse]:
        docs = await self._repo.find_by_status(status)
        return [
            TaskResponse(
                id=str(d.id), title=d.title, description=d.description,
                priority=d.priority, status=d.status, assignee=d.assignee,
            )
            for d in docs
        ]


# --- Controller ---

from pyfly.container import rest_controller
from pyfly.kernel.exceptions import ResourceNotFoundException
from pyfly.web import (
    request_mapping, get_mapping, post_mapping, delete_mapping,
    exception_handler, PathVar, QueryParam, Valid,
)


@rest_controller
@request_mapping("/api/tasks")
class TaskController:
    def __init__(self, task_service: TaskService) -> None:
        self._service = task_service

    @get_mapping("/")
    async def list_tasks(self, status: QueryParam[str] = None) -> list[TaskResponse]:
        if status:
            return await self._service.find_by_status(status)
        return await self._service.find_by_status("TODO")

    @get_mapping("/{task_id}")
    async def get_task(self, task_id: PathVar[str]) -> TaskResponse:
        task = await self._service.find_by_id(task_id)
        if task is None:
            raise ResourceNotFoundException(f"Task {task_id} not found")
        return task

    @post_mapping("/", status_code=201)
    async def create_task(self, body: Valid[CreateTaskRequest]) -> TaskResponse:
        return await self._service.create(body)

    @exception_handler(ResourceNotFoundException)
    async def handle_not_found(self, exc: ResourceNotFoundException):
        return 404, {"error": {"message": str(exc), "code": "TASK_NOT_FOUND"}}
```

This example demonstrates:
- `Valid[CreateTaskRequest]` for structured 422 validation errors on POST
- `PathVar[str]` for path parameter binding
- `QueryParam[str]` for optional query parameter filtering
- `@exception_handler` for controller-level error handling
- Derived query methods on the repository (`find_by_status`, `find_by_assignee_and_status`)

---

## Complete CRUD Example

The following example demonstrates a full Product document, repository with derived queries, service, and controller -- a complete vertical slice of a PyFly application using MongoDB.

```python
# ==========================================================================
# Document
# ==========================================================================

from pyfly.data.document.mongodb import BaseDocument
from beanie import Indexed, PydanticObjectId
from pydantic import Field


class ProductDocument(BaseDocument):
    """Product stored in the 'products' MongoDB collection."""

    name: str
    sku: Indexed(str, unique=True)
    description: str = ""
    price: float = Field(gt=0)
    category: Indexed(str)
    tags: list[str] = Field(default_factory=list)
    active: bool = True

    class Settings:
        name = "products"


# ==========================================================================
# Repository
# ==========================================================================

from pyfly.data.document.mongodb import MongoRepository
from pyfly.container import repository as repo_stereotype


@repo_stereotype
class ProductRepository(MongoRepository[ProductDocument, PydanticObjectId]):
    def __init__(self) -> None:
        super().__init__(ProductDocument)

    # --- Derived query methods (stubs, auto-compiled at startup) ---

    # Equals (default operator)
    async def find_by_category(self, category: str) -> list[ProductDocument]: ...

    # AND connector
    async def find_by_active_and_category(
        self, active: bool, category: str
    ) -> list[ProductDocument]: ...

    # Greater than + ordering
    async def find_by_price_greater_than_order_by_price_desc(
        self, min_price: float
    ) -> list[ProductDocument]: ...

    # Contains (case-insensitive regex)
    async def find_by_name_containing(self, fragment: str) -> list[ProductDocument]: ...

    # Count
    async def count_by_category(self, category: str) -> int: ...

    # Exists
    async def exists_by_sku(self, sku: str) -> bool: ...

    # Delete
    async def delete_by_active(self, active: bool) -> int: ...


# ==========================================================================
# Request / Response Models
# ==========================================================================

from pydantic import BaseModel


class CreateProductRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    sku: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    price: float = Field(..., gt=0)
    category: str
    tags: list[str] = Field(default_factory=list)


class UpdateProductRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    price: float = Field(..., gt=0)
    category: str
    tags: list[str] = Field(default_factory=list)


class ProductResponse(BaseModel):
    id: str
    name: str
    sku: str
    description: str
    price: float
    category: str
    tags: list[str]
    active: bool


# ==========================================================================
# Service
# ==========================================================================

from pyfly.container import service
from pyfly.data import Page, Pageable, Sort
from pyfly.kernel.exceptions import ResourceNotFoundException, ConflictException


@service
class ProductService:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    async def create(self, request: CreateProductRequest) -> ProductResponse:
        # Check for duplicate SKU
        if await self._repo.exists_by_sku(request.sku):
            raise ConflictException(
                f"Product with SKU '{request.sku}' already exists",
                code="DUPLICATE_SKU",
            )

        doc = ProductDocument(
            name=request.name,
            sku=request.sku,
            description=request.description,
            price=request.price,
            category=request.category,
            tags=request.tags,
        )
        saved = await self._repo.save(doc)
        return self._to_response(saved)

    async def find_by_id(self, product_id: str) -> ProductResponse:
        doc = await self._repo.find_by_id(product_id)
        if doc is None:
            raise ResourceNotFoundException(
                f"Product {product_id} not found",
                code="PRODUCT_NOT_FOUND",
            )
        return self._to_response(doc)

    async def find_all_active(
        self, category: str | None = None
    ) -> list[ProductResponse]:
        if category:
            docs = await self._repo.find_by_active_and_category(True, category)
        else:
            docs = await self._repo.find_all(active=True)
        return [self._to_response(d) for d in docs]

    async def find_paginated(
        self,
        page: int = 1,
        size: int = 20,
    ) -> Page[ProductResponse]:
        pageable = Pageable.of(
            page=page,
            size=size,
            sort=Sort.by("name"),
        )
        result = await self._repo.find_paginated(pageable=pageable)
        return result.map(self._to_response)

    async def search_by_name(self, query: str) -> list[ProductResponse]:
        docs = await self._repo.find_by_name_containing(query)
        return [self._to_response(d) for d in docs]

    async def update(
        self, product_id: str, request: UpdateProductRequest
    ) -> ProductResponse:
        doc = await self._repo.find_by_id(product_id)
        if doc is None:
            raise ResourceNotFoundException(
                f"Product {product_id} not found",
                code="PRODUCT_NOT_FOUND",
            )
        doc.name = request.name
        doc.description = request.description
        doc.price = request.price
        doc.category = request.category
        doc.tags = request.tags
        saved = await self._repo.save(doc)
        return self._to_response(saved)

    async def delete(self, product_id: str) -> None:
        await self._repo.delete(product_id)

    async def count_in_category(self, category: str) -> int:
        return await self._repo.count_by_category(category)

    async def find_expensive(self, min_price: float) -> list[ProductResponse]:
        docs = await self._repo.find_by_price_greater_than_order_by_price_desc(min_price)
        return [self._to_response(d) for d in docs]

    @staticmethod
    def _to_response(doc: ProductDocument) -> ProductResponse:
        return ProductResponse(
            id=str(doc.id),
            name=doc.name,
            sku=doc.sku,
            description=doc.description,
            price=doc.price,
            category=doc.category,
            tags=doc.tags,
            active=doc.active,
        )


# ==========================================================================
# Controller
# ==========================================================================

from pyfly.container import rest_controller
from pyfly.web import (
    request_mapping, get_mapping, post_mapping, put_mapping, delete_mapping,
    exception_handler, Body, PathVar, QueryParam, Valid,
)


@rest_controller
@request_mapping("/api/products")
class ProductController:

    def __init__(self, product_service: ProductService) -> None:
        self._service = product_service

    @get_mapping("/")
    async def list_products(
        self,
        category: QueryParam[str] = None,
        page: QueryParam[int] = 1,
        size: QueryParam[int] = 20,
    ) -> list[ProductResponse]:
        """List active products, optionally filtered by category."""
        return await self._service.find_all_active(category=category)

    @get_mapping("/{product_id}")
    async def get_product(self, product_id: PathVar[str]) -> ProductResponse:
        """Get a product by its ID."""
        return await self._service.find_by_id(product_id)

    @get_mapping("/search")
    async def search_products(
        self, q: QueryParam[str] = "",
    ) -> list[ProductResponse]:
        """Search products by name (case-insensitive contains)."""
        return await self._service.search_by_name(q)

    @get_mapping("/expensive")
    async def find_expensive(
        self, min_price: QueryParam[float] = 100.0,
    ) -> list[ProductResponse]:
        """Find products above a minimum price, sorted by price descending."""
        return await self._service.find_expensive(min_price)

    @post_mapping("/", status_code=201)
    async def create_product(self, body: Valid[CreateProductRequest]) -> ProductResponse:
        """Create a new product with Pydantic validation."""
        return await self._service.create(body)

    @put_mapping("/{product_id}")
    async def update_product(
        self,
        product_id: PathVar[str],
        body: Valid[UpdateProductRequest],
    ) -> ProductResponse:
        """Replace a product's mutable fields."""
        return await self._service.update(product_id, body)

    @delete_mapping("/{product_id}", status_code=204)
    async def delete_product(self, product_id: PathVar[str]) -> None:
        """Delete a product by ID."""
        await self._service.delete(product_id)

    # --- Exception Handlers ---

    @exception_handler(ResourceNotFoundException)
    async def handle_not_found(self, exc: ResourceNotFoundException):
        return 404, {
            "error": {
                "message": str(exc),
                "code": exc.code or "NOT_FOUND",
            }
        }

    @exception_handler(ConflictException)
    async def handle_conflict(self, exc: ConflictException):
        return 409, {
            "error": {
                "message": str(exc),
                "code": exc.code or "CONFLICT",
            }
        }


# ==========================================================================
# Application Bootstrap
# ==========================================================================

from pyfly.core import pyfly_application, PyFlyApplication
from pyfly.web import create_app
from pyfly.data.document.mongodb import initialize_beanie, MongoRepositoryBeanPostProcessor


@pyfly_application(
    name="product-service",
    version="1.0.0",
    scan_packages=["product_service"],
    description="Product catalog microservice backed by MongoDB",
)
class Application:
    pass


async def main():
    pyfly_app = PyFlyApplication(Application)
    await pyfly_app.startup()

    # Initialize Beanie with document models
    client = await initialize_beanie(
        uri="mongodb://localhost:27017",
        database="product_catalog",
        document_models=[ProductDocument],
    )

    # Register MongoDB post-processor for derived query methods
    pyfly_app.context.register_post_processor(MongoRepositoryBeanPostProcessor())

    # Create the web application
    app = create_app(
        title="Product Catalog",
        version="1.0.0",
        description="CRUD API for product management with MongoDB",
        context=pyfly_app.context,
        docs_enabled=True,
        actuator_enabled=True,
    )

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

**Configuration file (`pyfly.yaml`):**

```yaml
pyfly:
  app:
    name: product-service
    version: 1.0.0
    description: Product catalog microservice backed by MongoDB

  data:
    document:
      enabled: true
      uri: mongodb://localhost:27017
      database: product_catalog
      min_pool_size: 5
      max_pool_size: 50

  web:
    port: 8080
    docs:
      enabled: true
    actuator:
      enabled: true
```

This will expose:

- `GET    /api/products/`              -- list active products (with optional category filter)
- `GET    /api/products/{product_id}`  -- get a product by ID
- `GET    /api/products/search?q=...`  -- search products by name
- `GET    /api/products/expensive?min_price=...` -- find expensive products
- `POST   /api/products/`             -- create a product (with `Valid[T]` validation)
- `PUT    /api/products/{product_id}` -- update a product (with `Valid[T]` validation)
- `DELETE /api/products/{product_id}` -- delete a product
- `GET    /docs`                       -- Swagger UI
- `GET    /redoc`                      -- ReDoc
- `GET    /openapi.json`               -- OpenAPI 3.1 spec
- `GET    /actuator/health`            -- Health check

---

## Architecture Extensibility

The PyFly Data architecture is designed to support additional document database adapters (e.g., DynamoDB, Elasticsearch, Firestore) by implementing the same `QueryMethodCompilerPort` protocol that the SQLAlchemy and MongoDB adapters implement.

### QueryMethodCompilerPort Protocol

The `QueryMethodCompilerPort` is defined in `pyfly.data.ports.compiler`:

```python
from collections.abc import Callable, Coroutine
from typing import Any, Protocol, TypeVar

from pyfly.data.query_parser import ParsedQuery

T = TypeVar("T")


class QueryMethodCompilerPort(Protocol):
    """Compile a ParsedQuery into an async callable.

    Each data adapter (SQLAlchemy, MongoDB, DynamoDB, etc.) provides its own
    implementation. The shared QueryMethodParser produces ParsedQuery objects;
    this port compiles them into backend-specific executable queries.
    """

    def compile(
        self,
        parsed: ParsedQuery,
        entity: type[T],
    ) -> Callable[..., Coroutine[Any, Any, Any]]: ...
```

The protocol requires a single method: `compile(parsed, entity)`. It receives a `ParsedQuery` (which contains the prefix, predicates, connectors, and order clauses) and the entity/document type, and returns an async callable that executes the query.

This is a structural protocol (using `Protocol` from `typing`), so any class with a `compile` method matching this signature satisfies it -- no explicit inheritance required.

### Adding a New Document Database Adapter

To add support for a new document database (say, DynamoDB), you would:

1. **Create the adapter package:** `pyfly/data/document/dynamodb/`

2. **Implement a base document class** (analogous to `BaseDocument`):

```python
# pyfly/data/document/dynamodb/document.py
class BaseDynamoDocument:
    """Base document for DynamoDB items with audit fields."""
    created_at: datetime
    updated_at: datetime
    created_by: str | None = None
    updated_by: str | None = None
```

3. **Implement the repository** (analogous to `MongoRepository`):

```python
# pyfly/data/document/dynamodb/repository.py
class DynamoRepository(Generic[T, ID]):
    """Generic CRUD repository for DynamoDB."""
    async def save(self, entity: T) -> T: ...
    async def find_by_id(self, id: ID) -> T | None: ...
    async def find_all(self, **filters: Any) -> list[T]: ...
    async def delete(self, id: ID) -> None: ...
    async def count(self) -> int: ...
    async def exists(self, id: ID) -> bool: ...
    async def find_paginated(self, page=1, size=20, pageable=None) -> Page[T]: ...
```

4. **Implement the query compiler** (satisfying `QueryMethodCompilerPort`):

```python
# pyfly/data/document/dynamodb/query_compiler.py
from pyfly.data.query_parser import ParsedQuery


class DynamoQueryMethodCompiler:
    """Compile ParsedQuery into DynamoDB query/scan operations."""

    def compile(self, parsed: ParsedQuery, entity: type[T]) -> Callable[..., Coroutine]:
        # Translate parsed predicates into DynamoDB expressions
        # e.g., "eq" -> Key("field").eq(value)
        # e.g., "gt" -> Key("field").gt(value)
        # e.g., "containing" -> Attr("field").contains(value)
        ...
```

5. **Implement the post-processor** (analogous to `MongoRepositoryBeanPostProcessor`):

```python
# pyfly/data/document/dynamodb/post_processor.py
class DynamoRepositoryBeanPostProcessor:
    def __init__(self) -> None:
        self._query_parser = QueryMethodParser()
        self._query_compiler = DynamoQueryMethodCompiler()

    def after_init(self, bean, bean_name):
        if not isinstance(bean, DynamoRepository):
            return bean
        # Parse and compile derived query methods, same pattern as MongoDB
        ...
```

6. **Add auto-detection** in `AutoConfiguration`:

```python
@staticmethod
def detect_dynamodb_provider() -> str:
    if AutoConfiguration.is_available("aiobotocore"):
        return "dynamodb"
    return "none"
```

The key insight is that the `QueryMethodParser` is fully shared -- you never need to reimplement the parsing logic. The parser produces `ParsedQuery` objects that are backend-agnostic. Your adapter only needs to compile those parsed queries into the target database's query format.

This architecture means that the naming convention for derived query methods (`find_by_status_and_role_order_by_name_desc`) is consistent across all PyFly data adapters. Once you learn the convention, it works the same way whether your backend is PostgreSQL, MongoDB, DynamoDB, or any future adapter.

Source files:
- `src/pyfly/data/ports/compiler.py` -- `QueryMethodCompilerPort` protocol
- `src/pyfly/data/query_parser.py` -- `QueryMethodParser` (shared)
- `src/pyfly/data/document/mongodb/query_compiler.py` -- `MongoQueryMethodCompiler` (MongoDB implementation)
- `src/pyfly/data/relational/sqlalchemy/query_compiler.py` -- `QueryMethodCompiler` (SQLAlchemy implementation)
