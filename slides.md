---
# You can also start simply with 'default'
theme: default
# some information about your slides (markdown enabled)
title: Welcome to Slidev
info: |
  ## Slidev Starter Template
  Presentation slides for developers.
  Learn more at [Sli.dev](https://sli.dev)
# apply unocss classes to the current slide
class: text-center
# https://sli.dev/features/drawing
drawings:
  persist: false
# slide transition: https://sli.dev/guide/animations.html#slide-transitions
transition: slide-left
# enable MDC Syntax: https://sli.dev/features/mdc
mdc: true

---

# Getting Past "It Runs, So It’s Fine"

## Eight Common Python 3.12 Typing Mistakes (and How to Fix Them)

Django 5.1 backend engineering guild meeting

---

# Mistake 1 ‑‑ Unintentional Any Propagation

```python
# utils/db.py

from django.db import connection

def run_sql(sql: str, params: list) -> list:
  with connection.cursor() as cur:
    cur.execute(sql, params)
    return cur.fetchall() # ← mypy infers "list[Any]"
```

---

# What happened?

- fetchall() comes from an untyped stub, so its return type defaults to Any.
- That single Any silently spreads everywhere the result travels.

## Solution

- Add a return type that describes the rows – e.g. `list[tuple[int, str]]`.
- Pin a stub package (e.g. types-Django) or declare a TypedDict/Protocol for rows.
- Compile with --strict (mypy) or --warn‑unused‑ignores (pyright) to surface the leak.

```python
from typing import TypeAlias

Row: TypeAlias = tuple[int, str] # or a TypedDict when column‑named

def run_sql(sql: str, params: list[object]) -> list[Row]:
  pass
```

---

## zoom: 1.5

# Mistake 2 ‑‑ Overusing typing.cast

```python
# services/payments.py

from typing import cast
from decimal import Decimal

def as_dollars(amount: str | Decimal) -> Decimal:
  return cast(Decimal, amount) \* Decimal("0.01")
```

---

## zoom: 1.2

# What’s wrong?

- cast() lies to the type checker – it asserts the value is already a Decimal without runtime verification.
- If a str sneaks in, you get a TypeError.

## Better pattern

```python
def as_dollars(amount: str | Decimal) -> Decimal:
  if isinstance(amount, Decimal):
    return amount * Decimal("0.01")
  try:
    return Decimal(amount) * Decimal("0.01")
  except Exception as exc: # validation, not blind casting
    raise ValueError("Bad amount") from exc
```

---

zoom: 1.4
layout: center

---

# Mistake 3 ‑‑ Bare Containers (missing generics)

```python
def load_ids() -> list:
  with open("ids.txt") as fh:
    return [int(line) for line in fh]
```

---

# Why it matters

– `list` without `[...]` returns `list[Any]`; later code gets no help.

## Fix

```python
def load_ids() -> list[int]:
  ...
```

- Turn on `warn_bare_types` = true (mypy) or reportImplicitAny = true (pyright).

---

# Mistake 5 ‑‑ Mutable Default Values + Typing Confusion

```python
from dataclasses import dataclass

@dataclass
class Accumulator:
  seen: list[str] = []
```

---

# What's wrong?

- Runtime bug—all instances share one list.
- Typing confusion—default `[]` is fine syntactically but masks the shared‑state issue.

```python
from dataclasses import dataclass, field

@dataclass
class Accumulator:
  seen: list[str] = field(default_factory=list)
```

- Linters like ruff‑b013 or mypy’s --strict-equality flag prevent this.

---

# Mistake 6 ‑‑ Ignoring Self for Fluent APIs

```python
class QueryBuilder:
  def filter(self, **kw) -> "QueryBuilder":
    ...
    return self

  def eager(self) -> "QueryBuilder":
    ...
    return self
```

---

# What's wrong?

- Using literal string annotations works, but Python 3.12 offers `typing.Self` – clearer & future‑proof.

```python
from typing import Self

class QueryBuilder:
  def filter(self, **kw) -> Self:
    ...
    return self

  def eager(self) -> Self:
    ...
    return self
```

- Now subclasses inherit the correct return type automatically.

---

# Mistake 7 ‑‑ Untyped Django QuerySets

```python
users = User.objects.filter(is_active=True) # inferred as QuerySet[Any]

def first_email() -> str:
  return users[0].email
```

---

# How to fix?

- Install django-stubs or types-Django so .objects returns `QuerySet[User]`.
- Or annotate yourself:

```python
from django.db.models import QuerySet

users: QuerySet[User] = User.objects.filter(is_active=True)

def first_email() -> str:
  return users[0].email
```

---

# Mistake 8 ‑‑ Over‑wide Unions Instead of Protocols

```python
def to_jsonable(obj: str | int | float | Decimal) -> str | int | float:
  if isinstance(obj, Decimal):
    return float(obj)
  return obj
```

---

# What's wrong?

- API really wants "anything that can become an int" or "has **float**" &rarr; use a `Protocol`.

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class SupportsJSON(Protocol):
  def __float__(self) -> float: ...

def to_jsonable(obj: str | int | SupportsJSON) -> str | int | float:
  if isinstance(obj, SupportsJSON):
    return float(obj)
  return obj
```

- Reduces union sprawl and tightens guarantees.

---

## zoom: 1.4

# Mistake 9 — Confusing Any with Unknown

```python
from typing import Any
import json, pathlib

def load_conf(path: pathlib.Path | str) -> Any:
    with open(path) as fh:
        return json.load(fh)          # 👈 returns "Any"
```

---

# Key difference

<table>
  <tr><th>Any</th><th>Unknown</th></tr>
  <tr><td>Opt-out: all operations are allowed; errors are suppressed</td><td>Opt-in: no operation is allowed until the value is narrowed or cast.</td></tr>
  <tr><td>Spreads silently, hiding type holes.</td><td>Shines a spotlight on every place you forgot a real type.</td></tr>
</table>

Pyright defaults to Unknown when inference fails - exactly to expose "blind spots." ￼

---

## Better pattern

```python
def load_conf(path: Path | str) -> Unknown: # ← explicit
  data = json.loads(Path(path).read_text())

  # Validate/narrow before use
  if not isinstance(data, dict) or "version" not in data:
      raise ValueError("bad config format")

  assert_type(data, dict[str, Unknown]) # editor helper
  return data
```

## Practical tips

- Run Pyright in --strict mode so implicit Any becomes Unknown.
- Keep typed-stub deps current (e.g. pip install --upgrade django-stubs) so external libraries don’t leak Any.

---

# Mistake 10 — Relying on hasattr / getattr Without Telling the Type Checker

```python
def tally(obj, count: int) -> int:
    if hasattr(obj, "total"):           # duck-typing at runtime
        return obj.total + count        # 🔴 pyright: "obj" still Any
    raise TypeError("object missing total")
```

---

# Why it backfires

- The runtime hasattr check does ensure the attribute exists, but the type checker can’t see that guarantee—obj stays `Any`/`Unknown`, so no help or safety.
- Two robust options

## 1. Structural Protocol

```python
from typing import Protocol

class HasTotal(Protocol):
    total: int

def tally(obj: HasTotal, count: int) -> int:
    return obj.total + count
```

Any object with an int .total now passes, and misuse is caught at call-site.

---

## 2. Custom TypeGuard

```python
from typing import TypeGuard

def has_total(x: object) -> TypeGuard["HasTotal"]:
    return hasattr(x, "total") and isinstance(getattr(x, "total"), int)

def tally(obj: object, count: int) -> int:
    if has_total(obj):               # type narrows here ✔
        return obj.total + count
    raise TypeError("object missing total")
```

- TypeGuard communicates the narrowing contract directly to the checker.

## Take-away

Whenever you branch on attribute presence or value, express that promise to the type system—either with a Protocol for cheap "duck typing" or a TypeGuard when the assertion is non-trivial.

---

# Workflow Trick - Using `reveal_type` for Instant Feedback

```python
# debugging_types.py
from typing import assert_type, reveal_type

def maybe_dict(flag: bool):
  if flag:
    data = {"key": 1}
  else:
    data = ["fallback"]

  reveal_type(data)
  assert_type(data, dict[str, int] | list[str])
  return data
```

- Sanity check while spiking code or refactoring
- Immediately surfaces surprise `Any`/`Unknown` leaks
- Combine with `assert_type()` to lock in expectations and catch regressions in CI.

---

# Key take‑aways

1. Compile in strict mode; don’t patch the holes later.
2. Treat `Any` and unchecked `cast()` like run‑time `eval()`—they break guarantees.
3. Prefer precise, minimal types over “works for everything” unions.
4. Lean on newer features (Self, `assert_never`, TypeAlias, TypeVarTuple, …).
5. Keep stubs up to date: django-stubs, types‑requests, etc.
6. Validate at boundaries; trust types inside the boundary.

