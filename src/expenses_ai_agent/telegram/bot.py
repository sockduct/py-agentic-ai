import logging

from decouple import config
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from expenses_ai_agent.llms.openai import OpenAIAssistant
from expenses_ai_agent.services.classification import ClassificationService
from expenses_ai_agent.storage.repo import DBExpenseRepo
from expenses_ai_agent.telegram.handlers import (
    handle_category_selection,
    handle_expense_text,
    help_command,
    start_command,
)
from expenses_ai_agent.telegram.keyboards import CATEGORY_CALLBACK_PREFIX

logger = logging.getLogger(__name__)


def build_application(token: str, db_url: str, api_key: str) -> Application:
    application = Application.builder().token(token).build()

    assistant = OpenAIAssistant(api_key=api_key)
    repo = DBExpenseRepo(db_url)
    try:
        application.bot_data["service"] = ClassificationService(assistant, repo)

        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(
            CallbackQueryHandler(
                handle_category_selection, pattern=f"^{CATEGORY_CALLBACK_PREFIX}"
            )
        )
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_expense_text)
        )
        return application
    except Exception:
        repo.close()
        raise


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    token = config("TELEGRAM_BOT_TOKEN")
    db_url = config("DATABASE_URL", default="sqlite:///./expenses.db")
    api_key = config("OPENAI_API_KEY")

    application = build_application(token=token, db_url=db_url, api_key=api_key)
    service: ClassificationService = application.bot_data["service"]
    try:
        logger.info("Starting bot polling...")
        application.run_polling(
            allowed_updates=Update.ALL_TYPES, drop_pending_updates=True
        )
    finally:
        if isinstance(service.expense_repo, DBExpenseRepo):
            service.expense_repo.close()


if __name__ == "__main__":
    main()
