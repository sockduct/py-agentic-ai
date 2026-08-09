from unittest.mock import MagicMock, create_autospec, patch

import pytest

from expenses_ai_agent.llms.base import Assistant
from expenses_ai_agent.services.classification import ClassificationService
from expenses_ai_agent.storage.repo import DBExpenseRepo
from expenses_ai_agent.telegram import bot as telegram_bot


class TestTelegramBotLifecycle:
    def test_build_application_registers_handlers_and_service(self):
        repo = create_autospec(DBExpenseRepo, instance=True)
        application = MagicMock()
        application.bot_data = {}
        builder = MagicMock()
        builder.token.return_value = builder
        builder.build.return_value = application

        with (
            patch.object(telegram_bot.Application, "builder", return_value=builder),
            patch.object(telegram_bot, "OpenAIAssistant") as assistant_cls,
            patch.object(telegram_bot, "DBExpenseRepo", return_value=repo),
        ):
            result = telegram_bot.build_application(
                token="token", db_url="sqlite://", api_key="api-key"
            )

        assert result is application
        builder.token.assert_called_once_with("token")
        assistant_cls.assert_called_once_with(api_key="api-key")
        assert application.bot_data["service"].expense_repo is repo
        assert application.add_handler.call_count == 5
        repo.close.assert_not_called()

    def test_main_closes_owned_repo_after_polling(self):
        repo = DBExpenseRepo("sqlite:///:memory:")
        service = ClassificationService(
            assistant=create_autospec(Assistant), expense_repo=repo
        )
        application = MagicMock()
        application.bot_data = {"service": service}

        with (
            patch.object(telegram_bot, "config", return_value="configured"),
            patch.object(telegram_bot, "build_application", return_value=application),
        ):
            telegram_bot.main()

        assert not repo.is_open()
        assert DBExpenseRepo._owned_instance is None

    def test_main_closes_owned_repo_when_polling_fails(self):
        repo = DBExpenseRepo("sqlite:///:memory:")
        service = ClassificationService(
            assistant=create_autospec(Assistant), expense_repo=repo
        )
        application = MagicMock()
        application.bot_data = {"service": service}
        application.run_polling.side_effect = RuntimeError("polling failed")

        with (
            patch.object(telegram_bot, "config", return_value="configured"),
            patch.object(telegram_bot, "build_application", return_value=application),
            pytest.raises(RuntimeError, match="polling failed"),
        ):
            telegram_bot.main()

        assert not repo.is_open()
        assert DBExpenseRepo._owned_instance is None

    def test_build_application_closes_repo_when_setup_fails(self):
        repo = create_autospec(DBExpenseRepo, instance=True)
        application = MagicMock()
        application.bot_data = {}
        application.add_handler.side_effect = RuntimeError("handler setup failed")
        builder = MagicMock()
        builder.token.return_value = builder
        builder.build.return_value = application

        with (
            patch.object(telegram_bot.Application, "builder", return_value=builder),
            patch.object(telegram_bot, "OpenAIAssistant"),
            patch.object(telegram_bot, "DBExpenseRepo", return_value=repo),
            pytest.raises(RuntimeError, match="handler setup failed"),
        ):
            telegram_bot.build_application("token", "sqlite://", "api-key")

        repo.close.assert_called_once_with()
