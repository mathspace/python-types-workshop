

from typing import NewType, reveal_type


UserId = NewType('UserId', int)  # Makes UserId a *subtype* of int, not an Alias


def get_user_name(user_id: UserId) -> str:
    return "John Doe"


user_id = UserId(1)
print(get_user_name(user_id))
print(get_user_name(1))  # type error

x = UserId(1) + UserId(2)  # No type error, but reveal_type(x) is int
reveal_type(x)
