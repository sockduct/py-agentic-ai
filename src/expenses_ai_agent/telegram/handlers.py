from telegram import Update
from telegram.ext import ContextTypes

from expenses_ai_agent.storage.models import ExpenseCategory
from expenses_ai_agent.telegram.keyboards import build_category_confirmation_keyboard

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


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text(WELCOME_TEXT)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text(HELP_TEXT)


async def handle_expense_text(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if not update.message or not update.message.text:
        return
    service = context.bot_data["service"]
    text = update.message.text
    result = service.classify(text)

    if context.user_data is not None:
        context.user_data["expense_description"] = text
        context.user_data["classification_response"] = result.response

    keyboard = build_category_confirmation_keyboard(
        suggested_category=result.response.category,
        all_categories=[c.value for c in ExpenseCategory],
    )
    await update.message.reply_text(
        f"Classified as {result.response.category} "
        f"({result.response.confidence:.0%} confidence)\n"
        f"Amount: {result.response.total_amount} {result.response.currency}",
        reply_markup=keyboard,
    )


async def handle_category_selection(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    if not query or not query.data or not update.effective_user:
        return
    await query.answer()  # stop the spinner first, always
    category = query.data.split(":", 1)[1]  # "category:Food" -> "Food"

    user_data = context.user_data or {}
    description = user_data.get("expense_description")
    response = user_data.get("classification_response")
    if description is None or response is None:
        await query.edit_message_text("Session expired. Send the expense again.")
        return

    service = context.bot_data["service"]
    service.persist_with_category(
        expense_description=description,
        category_name=category,
        response=response,
        telegram_user_id=update.effective_user.id,
    )
    await query.edit_message_text(f"Saved as {category}!")
