class ExpenseNotFoundError(Exception):
    """Taking an argument and calling super not required but doing anyway..."""

    def __init__(self, msg: int | str) -> None:
        self.msg = str(msg) if isinstance(msg, int) else msg
        super().__init__(self.msg)


class InvalidExpenseCategory(Exception):
    """An expense category was passed that's not in ExpenseCategory"""

    pass
