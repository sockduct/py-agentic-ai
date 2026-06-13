from typing import Any


class ExpenseNotFoundError(Exception):
    """Taking an argument and calling super not required but doing anyway..."""

    # Note:  msg should be a string, but using Any to allow for other types
    #        like int.  Don't want strict type checking and an Exception when
    #        already in an Exception...
    def __init__(self, msg: Any) -> None:
        self.msg = str(msg)
        super().__init__(self.msg)
