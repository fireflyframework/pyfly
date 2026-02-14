# Validation Guide

PyFly integrates deeply with [Pydantic](https://docs.pydantic.dev/) to provide
declarative input validation throughout your application. This guide covers the
validation helpers, decorators, and their integration with the web layer.

---

## Table of Contents

1. [Introduction](#introduction)
2. [validate_model()](#validate_model)
   - [Basic Usage](#basic-usage)
   - [Field Error Handling](#field-error-handling)
3. [@validate_input Decorator](#validate_input-decorator)
   - [Parameters](#parameters)
   - [How It Works](#how-it-works)
   - [Passthrough Behavior](#passthrough-behavior)
4. [@validator Decorator](#validator-decorator)
   - [Predicate Functions](#predicate-functions)
   - [Lambda Predicates](#lambda-predicates)
5. [ValidationException](#validationexception)
6. [Integration with the Web Layer](#integration-with-the-web-layer)
   - [Body[T] Automatic Validation](#bodyt-automatic-validation)
   - [Automatic 422 Responses](#automatic-422-responses)
7. [Complete Example](#complete-example)

---

## Introduction

Validation is the first line of defense against invalid data entering your system.
PyFly provides three complementary validation mechanisms:

| Mechanism         | Purpose                                          | Module                         |
|-------------------|--------------------------------------------------|--------------------------------|
| `validate_model()` | Validate a raw dict against a Pydantic model     | `pyfly.validation.helpers`     |
| `@validate_input` | Decorator for automatic parameter validation     | `pyfly.validation.decorators`  |
| `@validator`      | Decorator for custom predicate-based validation  | `pyfly.validation.decorators`  |

All three raise `ValidationException` on failure, which the web layer automatically
converts to a `422 Unprocessable Entity` response with structured error details.

```python
from pyfly.validation import validate_model, validate_input, validator
```

**Source:** `src/pyfly/validation/__init__.py`

---

## validate_model()

`validate_model()` is the core validation function. It takes a Pydantic model class
and a plain Python dictionary, validates the dictionary against the model's schema,
and returns a fully constructed model instance on success.

### Basic Usage

```python
from pydantic import BaseModel
from pyfly.validation import validate_model


class CreateUserRequest(BaseModel):
    name: str
    email: str
    age: int


# Valid data -- returns a CreateUserRequest instance
user = validate_model(CreateUserRequest, {
    "name": "Alice",
    "email": "alice@example.com",
    "age": 30,
})
print(user.name)   # "Alice"
print(user.email)  # "alice@example.com"
print(user.age)    # 30
```

**Parameters:**

| Parameter | Type               | Description                                 |
|-----------|--------------------|---------------------------------------------|
| `model`   | `type[T]`          | A Pydantic `BaseModel` subclass             |
| `data`    | `dict[str, Any]`   | The raw dictionary to validate              |

**Returns:** An instance of `T` (the validated model).

**Raises:** `ValidationException` when validation fails.

Internally, the function delegates to Pydantic's `model_validate()` method:

```python
def validate_model(model: type[T], data: dict[str, Any]) -> T:
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        errors = exc.errors()
        detail = "; ".join(
            f"{'.'.join(str(loc) for loc in e['loc'])}: {e['msg']}" for e in errors
        )
        raise ValidationException(
            f"Validation failed: {detail}",
            code="VALIDATION_ERROR",
            context={"errors": errors},
        ) from exc
```

**Source:** `src/pyfly/validation/helpers.py`

### Field Error Handling

When validation fails, `validate_model()` constructs a `ValidationException` with:

- A human-readable `message` that joins all field errors with semicolons.
- An error `code` of `"VALIDATION_ERROR"`.
- A `context` dict containing the raw Pydantic error list under the key `"errors"`.

```python
from pyfly.kernel.exceptions import ValidationException

try:
    validate_model(CreateUserRequest, {
        "name": "",
        "email": "not-an-email",
        # "age" is missing entirely
    })
except ValidationException as exc:
    print(exc)
    # "Validation failed: age: Field required"

    print(exc.code)
    # "VALIDATION_ERROR"

    print(exc.context["errors"])
    # [{"type": "missing", "loc": ["age"], "msg": "Field required", ...}]
```

The `context["errors"]` list contains Pydantic's native error dictionaries. Each
error has these fields:

| Field   | Description                                       |
|---------|---------------------------------------------------|
| `type`  | Error type identifier (e.g. `"missing"`, `"string_type"`) |
| `loc`   | Location path as a list (e.g. `["age"]` or `["address", "zip"]`) |
| `msg`   | Human-readable error message                      |
| `input` | The input value that failed validation            |

For nested models, the `loc` path reflects the nesting:

```python
class Address(BaseModel):
    zip_code: str

class Order(BaseModel):
    shipping: Address

try:
    validate_model(Order, {"shipping": {"zip_code": 12345}})
except ValidationException as exc:
    for error in exc.context["errors"]:
        print(error["loc"])  # ["shipping", "zip_code"]
        print(error["msg"])  # "Input should be a valid string"
```

---

## @validate_input Decorator

The `@validate_input` decorator validates a specific keyword argument of an async
function against a Pydantic model. If the argument is a raw dict, the decorator
converts it to a validated model instance before the function executes.

```python
from pydantic import BaseModel
from pyfly.validation import validate_input


class OrderRequest(BaseModel):
    product_id: str
    quantity: int


@validate_input(model=OrderRequest, param="order_data")
async def create_order(order_data: OrderRequest) -> dict:
    return {
        "product_id": order_data.product_id,
        "quantity": order_data.quantity,
        "status": "created",
    }


# Call with a raw dict -- it gets validated and converted automatically
result = await create_order(order_data={"product_id": "SKU-42", "quantity": 3})
# result == {"product_id": "SKU-42", "quantity": 3, "status": "created"}
```

### Parameters

| Parameter | Type              | Description                                         |
|-----------|-------------------|-----------------------------------------------------|
| `model`   | `type[BaseModel]` | The Pydantic model class to validate against        |
| `param`   | `str`             | The name of the keyword argument to validate        |

### How It Works

The decorator wraps the function with logic that:

1. Looks up `kwargs[param]` (the named keyword argument).
2. If the value is `None`, the function is called as-is (no validation occurs).
3. If the value is a `dict`, it is passed through `validate_model(model, value)`.
   On success, the validated model instance replaces the dict in `kwargs`.
4. If the value is already an instance of the model, it passes through untouched.
5. The decorated function is then awaited with the (potentially replaced) kwargs.

The implementation:

```python
@functools.wraps(func)
async def wrapper(*args: Any, **kwargs: Any) -> Any:
    value = kwargs.get(param)
    if value is not None and isinstance(value, dict):
        kwargs[param] = validate_model(model, value)
    return await func(*args, **kwargs)
```

### Passthrough Behavior

If the argument is already a model instance, no validation occurs -- it passes
through directly:

```python
# This also works -- the model instance passes through
order = OrderRequest(product_id="SKU-42", quantity=3)
result = await create_order(order_data=order)
```

This is useful when calling the function from tests or other service methods where
you have already constructed a validated model.

**Source:** `src/pyfly/validation/decorators.py`

---

## @validator Decorator

The `@validator` decorator applies a custom predicate function to the arguments of
an async function. If the predicate returns `False`, a `ValidationException` is
raised with the specified message.

```python
from pyfly.validation import validator


@validator(
    predicate=lambda self, amount: amount > 0,
    message="Amount must be positive",
)
async def process_payment(self, amount: float) -> dict:
    return {"amount": amount, "status": "processed"}
```

### Predicate Functions

The predicate receives the **same positional and keyword arguments** as the decorated
function. It should return `True` if the arguments are valid and `False` otherwise.

```python
def positive_quantity(self, product_id: str, quantity: int) -> bool:
    """Validate that quantity is positive."""
    return quantity > 0


@validator(predicate=positive_quantity, message="Quantity must be positive")
async def add_to_cart(self, product_id: str, quantity: int) -> dict:
    return {"product_id": product_id, "quantity": quantity}
```

**Parameters:**

| Parameter   | Type                      | Default              | Description                    |
|-------------|---------------------------|----------------------|--------------------------------|
| `predicate` | `Callable[..., bool]`     | required             | Validation function            |
| `message`   | `str`                     | `"Validation failed"` | Error message on failure      |

When validation fails, the decorator raises:

```python
ValidationException(message, code="VALIDATION_ERROR")
```

### Lambda Predicates

For simple checks, lambda predicates keep the code concise:

```python
@validator(
    predicate=lambda self, start, end: start < end,
    message="Start date must be before end date",
)
async def create_booking(self, start: str, end: str) -> dict:
    return {"start": start, "end": end}
```

You can also combine multiple conditions:

```python
@validator(
    predicate=lambda self, amount, currency: (
        amount > 0 and amount <= 999999 and currency in ("USD", "EUR", "GBP")
    ),
    message="Invalid amount or unsupported currency",
)
async def initiate_transfer(self, amount: float, currency: str) -> dict:
    return {"amount": amount, "currency": currency}
```

### Stacking Multiple Validators

Multiple `@validator` decorators can be stacked. They execute from bottom to top
(the innermost decorator runs first):

```python
@validator(
    predicate=lambda self, price, qty: price * qty <= 10000,
    message="Order total must not exceed $10,000",
)
@validator(
    predicate=lambda self, price, qty: qty > 0,
    message="Quantity must be positive",
)
async def place_order(self, price: float, qty: int) -> dict:
    return {"total": price * qty}
```

**Source:** `src/pyfly/validation/decorators.py`

---

## ValidationException

All validation mechanisms in PyFly raise `ValidationException` on failure. This
exception is part of PyFly's structured exception hierarchy:

```
PyFlyException
  -> BusinessException
       -> ValidationException
```

**Constructor:**

```python
ValidationException(
    message: str,
    code: str | None = None,
    context: dict | None = None,
)
```

| Field     | Type           | Description                                     |
|-----------|----------------|-------------------------------------------------|
| `message` | `str`          | Human-readable error description                |
| `code`    | `str \| None`   | Machine-readable error code (e.g. `"VALIDATION_ERROR"`) |
| `context` | `dict`         | Structured error details (e.g. Pydantic errors) |

When raised by `validate_model()`, the context contains Pydantic's error list:

```python
{
    "errors": [
        {"type": "missing", "loc": ["field_name"], "msg": "Field required", ...},
        ...
    ]
}
```

When raised by `@validator`, the context is empty by default (since the predicate
only returns True/False, no field-level details are available).

**Source:** `src/pyfly/kernel/exceptions.py`

---

## Integration with the Web Layer

### Body[T] Automatic Validation

When you annotate a controller handler parameter with `Body[T]` where `T` is a
Pydantic `BaseModel`, PyFly automatically:

1. Reads the JSON request body.
2. Validates the JSON against the model `T`.
3. Passes the validated model instance to your handler.

```python
from pydantic import BaseModel, Field
from pyfly.container import rest_controller
from pyfly.web import request_mapping, post_mapping, Body


class CreateOrderRequest(BaseModel):
    customer_id: str
    items: list[dict] = Field(min_length=1)
    notes: str = ""


@rest_controller
@request_mapping("/api/orders")
class OrderController:

    @post_mapping("", status_code=201)
    async def create_order(self, body: Body[CreateOrderRequest]) -> dict:
        # `body` is a validated CreateOrderRequest instance
        return {
            "customer_id": body.customer_id,
            "item_count": len(body.items),
            "status": "created",
        }
```

### Automatic 422 Responses

When `Body[T]` validation fails, the global exception handler catches the resulting
`ValidationException` and returns a structured `422 Unprocessable Entity` response:

```json
{
    "error": {
        "message": "Validation failed: customer_id: Field required; items: List should have at least 1 item after validation, not 0",
        "code": "VALIDATION_ERROR",
        "transaction_id": "tx-abc-123",
        "timestamp": "2026-01-15T10:30:00Z",
        "status": 422,
        "path": "/api/orders",
        "context": {
            "errors": [
                {
                    "type": "missing",
                    "loc": ["customer_id"],
                    "msg": "Field required"
                },
                {
                    "type": "too_short",
                    "loc": ["items"],
                    "msg": "List should have at least 1 item after validation, not 0"
                }
            ]
        }
    }
}
```

This mapping is defined in the global exception handler at
`src/pyfly/web/adapters/starlette/errors.py`:

```python
_STATUS_MAP: dict[type, int] = {
    ValidationException: 422,
    # ... other exceptions
}
```

The same 422 response is produced whether the validation failure comes from
`Body[T]`, `validate_model()`, `@validate_input`, or `@validator`.

---

## Complete Example

The following example demonstrates a complete order validation workflow with nested
Pydantic models, custom validators, and full web integration.

```python
"""order_service/controllers.py"""

from pydantic import BaseModel, Field
from pyfly.container import rest_controller, service
from pyfly.web import request_mapping, post_mapping, get_mapping, Body, PathVar
from pyfly.validation import validate_model, validate_input, validator
from pyfly.kernel.exceptions import ValidationException, ResourceNotFoundException


# =========================================================================
# Pydantic Models
# =========================================================================

class Address(BaseModel):
    street: str
    city: str
    state: str = Field(min_length=2, max_length=2)
    zip_code: str = Field(pattern=r"^\d{5}(-\d{4})?$")


class OrderItem(BaseModel):
    product_id: str
    quantity: int = Field(gt=0, description="Must be at least 1")
    unit_price: float = Field(gt=0)


class CreateOrderRequest(BaseModel):
    customer_id: str
    shipping_address: Address
    items: list[OrderItem] = Field(min_length=1)
    notes: str = ""


# =========================================================================
# Service Layer
# =========================================================================

@service
class OrderService:
    """Order service with layered validation."""

    @validate_input(model=CreateOrderRequest, param="order_data")
    @validator(
        predicate=lambda self, order_data: (
            sum(item.quantity * item.unit_price
                for item in order_data.items) <= 10000
        ),
        message="Order total must not exceed $10,000",
    )
    async def create_order(self, order_data: CreateOrderRequest) -> dict:
        """Create a new order after validation."""
        total = sum(
            item.quantity * item.unit_price for item in order_data.items
        )
        return {
            "order_id": "ord-001",
            "customer_id": order_data.customer_id,
            "total": round(total, 2),
            "item_count": len(order_data.items),
            "shipping_city": order_data.shipping_address.city,
            "status": "created",
        }


# =========================================================================
# Controller Layer
# =========================================================================

@rest_controller
@request_mapping("/api/orders")
class OrderController:
    def __init__(self, order_service: OrderService) -> None:
        self._service = order_service

    @post_mapping("", status_code=201)
    async def create(self, body: Body[CreateOrderRequest]) -> dict:
        """Body[T] validates the JSON request automatically."""
        return await self._service.create_order(order_data=body)


# =========================================================================
# Manual Validation Example
# =========================================================================

async def manual_validation_demo():
    """Shows validate_model() used directly."""

    # Successful validation
    data = {
        "customer_id": "cust-42",
        "shipping_address": {
            "street": "123 Main St",
            "city": "Springfield",
            "state": "IL",
            "zip_code": "62701",
        },
        "items": [
            {"product_id": "SKU-001", "quantity": 2, "unit_price": 29.99},
            {"product_id": "SKU-002", "quantity": 1, "unit_price": 49.99},
        ],
    }
    order = validate_model(CreateOrderRequest, data)
    print(f"Validated: {order.customer_id}, {len(order.items)} items")

    # Failed validation -- invalid zip code, empty items
    try:
        validate_model(CreateOrderRequest, {
            "customer_id": "cust-99",
            "shipping_address": {
                "street": "456 Oak Ave",
                "city": "Portland",
                "state": "OR",
                "zip_code": "INVALID",
            },
            "items": [],
        })
    except ValidationException as exc:
        print(f"Error: {exc}")
        print(f"Code: {exc.code}")
        for error in exc.context["errors"]:
            loc = ".".join(str(part) for part in error["loc"])
            print(f"  {loc}: {error['msg']}")
```

**Testing the endpoint with `curl`:**

```bash
# Successful creation
curl -X POST http://localhost:8080/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cust-42",
    "shipping_address": {
      "street": "123 Main St",
      "city": "Springfield",
      "state": "IL",
      "zip_code": "62701"
    },
    "items": [
      {"product_id": "SKU-001", "quantity": 2, "unit_price": 29.99}
    ]
  }'
# HTTP 201
# {"order_id": "ord-001", "customer_id": "cust-42", "total": 59.98, ...}

# Validation failure -- missing required fields
curl -X POST http://localhost:8080/api/orders \
  -H "Content-Type: application/json" \
  -d '{"items": []}'
# HTTP 422
# {"error": {"message": "Validation failed: ...", "code": "VALIDATION_ERROR", ...}}
```
