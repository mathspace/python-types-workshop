# Django 5.1 + Python 3.12 Type Checking Best Practices

## Overview
This guide provides comprehensive best practices for implementing type checking in Django 5.1 projects using Python 3.12's latest typing features.

## 1. Django Models Type Checking

### Basic Model Type Annotations
```python
from django.db import models
from typing import Optional, ClassVar
from decimal import Decimal

class Product(models.Model):
    name: str = models.CharField(max_length=100)
    price: Decimal = models.DecimalField(max_digits=10, decimal_places=2)
    description: Optional[str] = models.TextField(blank=True, null=True)
    is_active: bool = models.BooleanField(default=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    
    # For QuerySet type hints
    objects: ClassVar[models.Manager["Product"]] = models.Manager()
    
    def __str__(self) -> str:
        return self.name
```

### Custom Manager with Type Hints
```python
from django.db import models
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models import QuerySet

class ProductManager(models.Manager["Product"]):
    def active(self) -> "QuerySet[Product]":
        return self.filter(is_active=True)
    
    def by_price_range(self, min_price: Decimal, max_price: Decimal) -> "QuerySet[Product]":
        return self.filter(price__gte=min_price, price__lte=max_price)

class Product(models.Model):
    # ... fields ...
    objects: ClassVar[ProductManager] = ProductManager()
```

## 2. Enum Fields with Type Checking

### Using Django's TextChoices with Proper Typing
```python
from django.db import models
from typing import TYPE_CHECKING

class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    SHIPPED = "shipped", "Shipped"
    DELIVERED = "delivered", "Delivered"
    CANCELLED = "cancelled", "Cancelled"

class Order(models.Model):
    status: OrderStatus = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )
    
    def can_cancel(self) -> bool:
        return self.status in [OrderStatus.PENDING, OrderStatus.PROCESSING]
```

### Custom Enum with Type Safety
```python
from enum import Enum
from typing import Literal

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

PriorityLiteral = Literal["low", "medium", "high", "urgent"]

class Task(models.Model):
    priority: PriorityLiteral = models.CharField(
        max_length=10,
        choices=[(p.value, p.name.title()) for p in Priority]
    )
    
    def is_urgent(self) -> bool:
        return self.priority == Priority.URGENT.value
```

## 3. Avoiding Any and Unknown

### Use Specific Types Instead of Any
```python
# Bad - Using Any
from typing import Any

def process_data(data: Any) -> Any:
    return data.some_method()

# Good - Using specific types
from typing import Protocol

class Processable(Protocol):
    def some_method(self) -> str: ...

def process_data(data: Processable) -> str:
    return data.some_method()
```

### Use Union Types for Multiple Possibilities
```python
from typing import Union
from django.contrib.auth.models import User

# Python 3.12 syntax
UserOrAnonymous = User | None

def get_user_display(user: UserOrAnonymous) -> str:
    if user is None:
        return "Anonymous"
    return user.get_full_name() or user.username
```

## 4. Type Checking Data from IO

### Request Data Validation
```python
from typing import TypedDict, NotRequired
from django.http import HttpRequest, JsonResponse
import json

class ProductCreateData(TypedDict):
    name: str
    price: float
    description: NotRequired[str]  # Optional field
    category_id: int

def create_product(request: HttpRequest) -> JsonResponse:
    try:
        data: ProductCreateData = json.loads(request.body)
    except (json.JSONDecodeError, KeyError) as e:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    # Type checker knows about the structure
    product = Product.objects.create(
        name=data["name"],
        price=Decimal(str(data["price"])),
        description=data.get("description", ""),
        category_id=data["category_id"]
    )
    
    return JsonResponse({"id": product.id})
```

### Using Pydantic for Complex Validation
```python
from pydantic import BaseModel, validator
from typing import Optional
from decimal import Decimal

class ProductSchema(BaseModel):
    name: str
    price: Decimal
    description: Optional[str] = None
    category_id: int
    
    @validator('price')
    def price_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError('Price must be positive')
        return v

def create_product_validated(request: HttpRequest) -> JsonResponse:
    try:
        data = ProductSchema.parse_raw(request.body)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    
    # data is now fully validated and typed
    product = Product.objects.create(**data.dict())
    return JsonResponse({"id": product.id})
```

## 5. Exhaustive Case Checking

### Using match/case for Enum Handling
```python
from typing import Never

def handle_order_status(status: OrderStatus) -> str:
    match status:
        case OrderStatus.PENDING:
            return "Order is awaiting processing"
        case OrderStatus.PROCESSING:
            return "Order is being prepared"
        case OrderStatus.SHIPPED:
            return "Order is in transit"
        case OrderStatus.DELIVERED:
            return "Order has been delivered"
        case OrderStatus.CANCELLED:
            return "Order has been cancelled"
        case _:
            # This will cause a type error if we miss a case
            assert_never(status)

def assert_never(value: Never) -> Never:
    raise AssertionError(f"Unexpected value: {value}")
```

### Using TypeGuard for Runtime Type Checking
```python
from typing import TypeGuard

def is_valid_status(status: str) -> TypeGuard[OrderStatus]:
    return status in [s.value for s in OrderStatus]

def process_status_string(status_str: str) -> str:
    if is_valid_status(status_str):
        # Type checker knows status_str is OrderStatus here
        return handle_order_status(status_str)
    raise ValueError(f"Invalid status: {status_str}")
```

## 6. Django Views with Type Safety

### Class-Based Views with Type Hints
```python
from django.views.generic import ListView, DetailView
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models import QuerySet

class ProductListView(ListView[Product]):
    model = Product
    template_name = "products/list.html"
    context_object_name = "products"
    
    def get_queryset(self) -> "QuerySet[Product]":
        return Product.objects.active().select_related("category")
```

### Function-Based Views with Type Safety
```python
from django.shortcuts import get_object_or_404
from django.http import HttpRequest, HttpResponse

def product_detail(request: HttpRequest, product_id: int) -> HttpResponse:
    product: Product = get_object_or_404(Product, id=product_id)
    context = {"product": product}
    return render(request, "products/detail.html", context)
```

## 7. Generic Types and Advanced Patterns

### Generic Repository Pattern
```python
from typing import Generic, TypeVar, TYPE_CHECKING
from django.db import models

if TYPE_CHECKING:
    from django.db.models import QuerySet

T = TypeVar("T", bound=models.Model)

class Repository(Generic[T]):
    def __init__(self, model: type[T]) -> None:
        self.model = model
    
    def find_by_id(self, id: int) -> T | None:
        try:
            return self.model.objects.get(id=id)
        except self.model.DoesNotExist:
            return None
    
    def find_all(self) -> "QuerySet[T]":
        return self.model.objects.all()

# Usage
product_repo = Repository(Product)
product = product_repo.find_by_id(1)  # Type: Product | None
```

### Protocol for Service Layer
```python
from typing import Protocol

class EmailService(Protocol):
    def send_email(self, to: str, subject: str, body: str) -> bool: ...

class OrderService:
    def __init__(self, email_service: EmailService) -> None:
        self.email_service = email_service
    
    def process_order(self, order: Order) -> bool:
        # Process order logic
        return self.email_service.send_email(
            order.customer.email,
            f"Order {order.id} confirmation",
            f"Your order has been processed."
        )
```

## 8. Testing with Type Safety

### Typed Test Cases
```python
from django.test import TestCase
from typing import cast

class ProductModelTest(TestCase):
    def setUp(self) -> None:
        self.product: Product = Product.objects.create(
            name="Test Product",
            price=Decimal("99.99"),
            description="Test description"
        )
    
    def test_product_creation(self) -> None:
        self.assertEqual(self.product.name, "Test Product")
        self.assertEqual(self.product.price, Decimal("99.99"))
    
    def test_can_cancel_order(self) -> None:
        order = Order.objects.create(
            product=self.product,
            status=OrderStatus.PENDING
        )
        self.assertTrue(order.can_cancel())
```

## 9. Configuration and Settings

### Type-Safe Settings
```python
from typing import Literal, TypedDict
from django.conf import settings

class DatabaseConfig(TypedDict):
    ENGINE: str
    NAME: str
    USER: str
    PASSWORD: str
    HOST: str
    PORT: int

Environment = Literal["development", "staging", "production"]

def get_environment() -> Environment:
    env = getattr(settings, "ENVIRONMENT", "development")
    if env not in ["development", "staging", "production"]:
        raise ValueError(f"Invalid environment: {env}")
    return env  # type: ignore
```

## 10. Performance Considerations

### Lazy Type Checking
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Heavy imports only for type checking
    from complex_module import ComplexType
    
def process_data(data: "ComplexType") -> str:
    # Implementation here
    pass
```

### Using `__future__` Annotations
```python
from __future__ import annotations
from django.db import models

class Category(models.Model):
    name: str = models.CharField(max_length=100)
    parent: Category | None = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
```

## 11. Tool Configuration

### mypy Configuration (mypy.ini)
```ini
[mypy]
python_version = 3.12
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
check_untyped_defs = True

[mypy-django.*]
ignore_missing_imports = True

[mypy-*.migrations.*]
ignore_errors = True
```

### Django-stubs Integration
```bash
pip install django-stubs[compatible-mypy]
```

## Summary

Key takeaways for type checking in Django projects:

1. **Use specific types**: Avoid `Any` and use `Union`, `Optional`, or `|` syntax
2. **Leverage Python 3.12 features**: Use new generic syntax and `match/case`
3. **Type your models**: Include `ClassVar` for managers and type hint fields
4. **Validate IO data**: Use `TypedDict`, Pydantic, or similar for request data
5. **Exhaustive checking**: Use `match/case` with `assert_never` for enums
6. **Generic patterns**: Use `Protocol` for structural typing
7. **Test with types**: Include type hints in test methods
8. **Performance**: Use `TYPE_CHECKING` for heavy imports
9. **Configuration**: Set up mypy and django-stubs properly

This approach provides robust type safety while maintaining Django's developer experience and performance.