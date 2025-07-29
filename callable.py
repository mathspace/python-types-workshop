from collections.abc import Callable
from collections.abc import Iterable

from typing import Protocol


def do_thing(on_success: Callable[[int], bool]) -> None:
    ...

def _success(x: int) -> bool:
    return True

do_thing(_success)


# Easy enough, but what about args and kwargs?
#
# First - it's a sign that you're doing something "complicated" if it's
# hard to specify the types.
#
# But if we really had to, we can use Protocol:

class Aggregator(Protocol):
    def __call__(self, *values: int, max_results: int | None = None) -> list[int]: ...


def process_numbers(data: Iterable[int], aggregator: Aggregator) -> list[int]:
    ...


def good_cb(*values: int, max_results: int | None = None) -> list[int]:
    ...

def bad_cb(*values: int, max_res: int | None) -> list[int]:
    ...

process_numbers([], good_cb)  # OK
process_numbers([], bad_cb)   # Type error: incompatible type, due to keyword argument type and name mismatch

