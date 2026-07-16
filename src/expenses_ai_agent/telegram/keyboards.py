from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from expenses_ai_agent.storage.models import Currency

CATEGORY_CALLBACK_PREFIX = "category:"
CURRENCY_CALLBACK_PREFIX = "setcurrency:"

SUPPORTED_CURRENCIES = [c.value for c in Currency]


def build_category_confirmation_keyboard(
    suggested_category: str,
    all_categories: list[str],
    columns: int = 3,
) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            text=f">> {cat} <<" if cat == suggested_category else cat,
            callback_data=f"{CATEGORY_CALLBACK_PREFIX}{cat}",
        )
        for cat in all_categories
    ]
    rows = [buttons[i : i + columns] for i in range(0, len(buttons), columns)]
    return InlineKeyboardMarkup(rows)


def build_currency_selection_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            text=code,
            callback_data=f"{CURRENCY_CALLBACK_PREFIX}{code}",
        )
        for code in SUPPORTED_CURRENCIES
    ]
    rows = [buttons[i : i + 3] for i in range(0, len(buttons), 3)]
    return InlineKeyboardMarkup(rows)
