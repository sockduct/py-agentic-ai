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

from expenses_ai_agent.llms.openai import OpenAIAssistant
from expenses_ai_agent.services.classification import ClassificationService
from expenses_ai_agent.services.preprocessing import InputPreprocessor
from expenses_ai_agent.storage.models import ExpenseCategory
from expenses_ai_agent.storage.repo import DBExpenseRepo
from expenses_ai_agent.telegram.keyboards import (
    CATEGORY_CALLBACK_PREFIX,
    build_category_confirmation_keyboard,
)

WELCOME_TEXT = (
    "Welcome! Send me an expense and I'll classify it.\n"
    "Example: Coffee at Starbucks $5.50\n\n"
    "Commands: /help"
)

HELP_TEXT = (
    "/start — welcome message\n"
    "/help — this message\n\n"
    "Or just send any expense description to classify it."
)


class ConversationState(IntEnum):
    WAITING_FOR_CATEGORY = 0


class ExpenseConversationHandler:
    def __init__(self, db_url: str, api_key: str, model: str = "gpt-4o-mini"):
        self._db_url = db_url
        self._api_key = api_key
        self._model = model
        self._preprocessor = InputPreprocessor()

    def _build_assistant(self) -> OpenAIAssistant:
        return OpenAIAssistant(api_key=self._api_key, model=self._model)

    def _build_service(self) -> ClassificationService:
        return ClassificationService(
            self._build_assistant(), DBExpenseRepo(self._db_url)
        )

    def _get_categories(self) -> list[str]:
        return [c.value for c in ExpenseCategory]

    def build(self) -> ConversationHandler:
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

        result = self._build_service().classify(processed.text)
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
        category = query.data.split(":", 1)[1]

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
