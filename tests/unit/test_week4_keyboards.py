from telegram import InlineKeyboardMarkup

from expenses_ai_agent.telegram.keyboards import (
    build_category_confirmation_keyboard,
    build_currency_selection_keyboard,
)


class TestCategoryKeyboard:
    def test_keyboard_returns_markup(self):
        keyboard = build_category_confirmation_keyboard(
            suggested_category="Food",
            all_categories=["Food", "Transport", "Entertainment"],
        )
        assert isinstance(keyboard, InlineKeyboardMarkup)

    def test_keyboard_has_all_categories(self):
        categories = ["Food", "Transport", "Entertainment", "Shopping"]
        keyboard = build_category_confirmation_keyboard("Food", categories)
        texts = [btn.text for row in keyboard.inline_keyboard for btn in row]
        for cat in categories:
            assert any(cat in t for t in texts)

    def test_keyboard_highlights_suggested(self):
        keyboard = build_category_confirmation_keyboard(
            "Transport", ["Food", "Transport", "Entertainment"]
        )
        buttons = [btn for row in keyboard.inline_keyboard for btn in row]
        transport = next(b for b in buttons if "Transport" in b.text)
        assert transport.text != "Transport"


class TestCurrencyKeyboard:
    def test_currency_keyboard_has_common_currencies(self):
        keyboard = build_currency_selection_keyboard()
        texts = " ".join(b.text for row in keyboard.inline_keyboard for b in row)
        assert "EUR" in texts and "USD" in texts and "GBP" in texts

    def test_currency_keyboard_has_callback_data(self):
        keyboard = build_currency_selection_keyboard()
        for b in (btn for row in keyboard.inline_keyboard for btn in row):
            assert b.callback_data
