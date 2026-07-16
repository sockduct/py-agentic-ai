import pytest

from expenses_ai_agent.services.preprocessing import (
    InputPreprocessor,
    PreprocessingResult,
)


class TestPreprocessingResult:
    def test_valid_result(self):
        result = PreprocessingResult(text="Coffee $5", is_valid=True, warnings=[])
        assert result.is_valid is True
        assert result.error is None

    def test_invalid_result(self):
        result = PreprocessingResult(
            text="ab", is_valid=False, warnings=[], error="Too short"
        )
        assert result.is_valid is False
        assert result.error is not None


class TestInputPreprocessor:
    @pytest.fixture
    def preprocessor(self):
        return InputPreprocessor()

    def test_valid_input(self, preprocessor):
        result = preprocessor.preprocess("Coffee at Starbucks $5.50")
        assert result.is_valid is True

    def test_too_short(self, preprocessor):
        assert preprocessor.preprocess("ab").is_valid is False

    def test_too_long(self, preprocessor):
        assert preprocessor.preprocess("a" * 501).is_valid is False

    def test_xss_script_rejected(self, preprocessor):
        assert (
            preprocessor.preprocess("Coffee <script>alert('xss')</script>").is_valid
            is False
        )

    def test_xss_javascript_rejected(self, preprocessor):
        assert preprocessor.preprocess("Check javascript:void(0)").is_valid is False

    def test_currency_symbol_normalized(self, preprocessor):
        result = preprocessor.preprocess("Coffee for $5.50")
        assert "USD" in result.text and "$" not in result.text

    def test_missing_amount_warns(self, preprocessor):
        result = preprocessor.preprocess("Coffee at cafe")
        assert result.is_valid is True and len(result.warnings) > 0
