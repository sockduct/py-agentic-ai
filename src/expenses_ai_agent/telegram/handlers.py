import warnings
from enum import IntEnum

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from telegram.warnings import PTBUserWarning

from expenses_ai_agent.llms.openai import OpenAIAssistant
from expenses_ai_agent.services.classification import ClassificationService
from expenses_ai_agent.services.preprocessing import InputPreprocessor
from expenses_ai_agent.storage.models import Currency, ExpenseCategory
from expenses_ai_agent.storage.repo import DBExpenseRepo, DBUserPreferenceRepo
from expenses_ai_agent.telegram.keyboards import (
    CATEGORY_CALLBACK_PREFIX,
    build_category_confirmation_keyboard,
    build_currency_selection_keyboard,
)

WELCOME_TEXT = (
    "Welcome! Send me an expense and I'll classify it.\n"
    "Example: Coffee at Starbucks $5.50\n\n"
    "Commands: /help"
)

HELP_TEXT = (
    "/start — welcome message\n"
    "/help — this message\n"
    "/currency — set your preferred currency\n"
    "/cancel — cancel the current operation\n\n"
    "Or just send any expense description to classify it."
)


class ConversationState(IntEnum):
    WAITING_FOR_CATEGORY = 0


class ExpenseConversationHandler:
    def __init__(
        self,
        db_url: str,
        api_key: str,
        model: str = "gpt-4o-mini",
        service: ClassificationService | None = None,
    ):
        self._db_url = db_url
        self._api_key = api_key
        self._model = model
        self._service = service
        self._preprocessor = InputPreprocessor()

    def _build_assistant(self) -> OpenAIAssistant:
        return OpenAIAssistant(api_key=self._api_key, model=self._model)

    def _build_service(self) -> ClassificationService:
        if self._service is not None:
            return self._service
        return ClassificationService(
            self._build_assistant(), DBExpenseRepo(self._db_url)
        )

    def _get_categories(self) -> list[str]:
        return [c.value for c in ExpenseCategory]

    def build(self) -> ConversationHandler:
        with warnings.catch_warnings(action="ignore", category=PTBUserWarning):
            return ConversationHandler(
                entry_points=[
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, self.handle_expense_text
                    )
                ],
                states={
                    ConversationState.WAITING_FOR_CATEGORY: [
                        CallbackQueryHandler(
                            self.handle_category_selection,
                            pattern=f"^{CATEGORY_CALLBACK_PREFIX}",
                        )
                    ],
                },
                fallbacks=[CommandHandler("cancel", cancel_command)],
            )

    async def handle_expense_text(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        if not update.message or not update.message.text:
            return ConversationHandler.END
        processed = self._preprocessor.preprocess(update.message.text)
        if not processed.is_valid:
            await update.message.reply_text(
                f"Sorry, I couldn't process that: {processed.error}"
            )
            return ConversationHandler.END
        if processed.warnings:
            await update.message.reply_text("Note: " + "; ".join(processed.warnings))

        try:
            result = self._build_service().classify(processed.text)
        except Exception:  # or narrow to (OpenAIError, ValidationError, ResponseError)
            await update.message.reply_text(
                "Sorry, I couldn't classify that. Please try again in a moment."
            )
            return ConversationHandler.END

        if context.user_data is not None:
            context.user_data["expense_description"] = processed.text
            context.user_data["classification_response"] = result.response

        keyboard = build_category_confirmation_keyboard(
            suggested_category=result.response.category,
            all_categories=self._get_categories(),
        )
        await update.message.reply_text(
            f"Classified as {result.response.category} "
            f"({result.response.confidence:.0%} confidence)\n"
            f"Amount: {result.response.total_amount} {result.response.currency}",
            reply_markup=keyboard,
        )
        return ConversationState.WAITING_FOR_CATEGORY

    async def handle_category_selection(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        query = update.callback_query
        if not query or not query.data or not update.effective_user:
            return ConversationHandler.END
        await query.answer()
        category = ExpenseCategory(query.data.split(":", 1)[1])

        user_data = context.user_data or {}
        description = user_data.get("expense_description")
        response = user_data.get("classification_response")
        if description is None or response is None:
            await query.edit_message_text("Session expired. Send the expense again.")
            return ConversationHandler.END

        self._build_service().persist_with_category(
            expense_description=description,
            category_name=category,
            response=response,
            telegram_user_id=update.effective_user.id,
        )
        await query.edit_message_text(f"Saved as {category}!")
        return ConversationHandler.END


class CurrencyHandler:
    def __init__(self, db_url: str):
        self._db_url = db_url

    async def currency_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not update.message:
            return
        await update.message.reply_text(
            "Select your preferred currency:",
            reply_markup=build_currency_selection_keyboard(),
        )

    async def handle_currency_selection(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = update.callback_query
        if not query or not query.data or not update.effective_user:
            return
        await query.answer()
        currency_code = query.data.split(":", 1)[1]
        with DBUserPreferenceRepo(self._db_url) as pref_repo:
            pref_repo.upsert(
                telegram_user_id=update.effective_user.id,
                currency=Currency(currency_code),
            )

        await query.edit_message_text(f"Currency preference saved as {currency_code}.")


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message:
        await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text(HELP_TEXT)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text(WELCOME_TEXT)
