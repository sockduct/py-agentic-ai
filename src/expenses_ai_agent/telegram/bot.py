import logging

from decouple import config
from telegram import Update
from telegram.ext import Application, CommandHandler

from expenses_ai_agent.telegram.handlers import (
    ExpenseConversationHandler,
    help_command,
    start_command,
)

logger = logging.getLogger(__name__)


def build_application(token: str, db_url: str, api_key: str) -> Application:
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(
        ExpenseConversationHandler(db_url=db_url, api_key=api_key).build()
    )
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
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
