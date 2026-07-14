import logging

from decouple import config
from telegram import Update
from telegram.ext import Application, CommandHandler

from expenses_ai_agent.llms.openai import OpenAIAssistant
from expenses_ai_agent.services.classification import ClassificationService
from expenses_ai_agent.storage.repo import DBExpenseRepo
from expenses_ai_agent.telegram.handlers import (
    ExpenseConversationHandler,
    help_command,
    start_command,
)

logger = logging.getLogger(__name__)


def build_application(token: str, db_url: str, api_key: str) -> Application:
    application = Application.builder().token(token).build()
    repo = DBExpenseRepo(db_url)

    try:
        service = ClassificationService(
            assistant=OpenAIAssistant(api_key=api_key), expense_repo=repo
        )
        application.bot_data["service"] = service
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(
            ExpenseConversationHandler(
                db_url=db_url, api_key=api_key, service=service
            ).build()
        )
    except Exception:
        repo.close()
        raise
    return application


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    token = config("TELEGRAM_BOT_TOKEN")
    db_url = config("DATABASE_URL", default="sqlite:///./expenses.db")
    api_key = config("OPENAI_API_KEY")

    application = build_application(token=token, db_url=db_url, api_key=api_key)
    logger.info("Starting bot polling...")
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES, drop_pending_updates=True
        )
    finally:
        service = application.bot_data.get("service")
        repo = getattr(service, "expense_repo", None)
        close = getattr(repo, "close", None)
        if callable(close):
            close()


if __name__ == "__main__":
    main()
