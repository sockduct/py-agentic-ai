from expenses_ai_agent.storage.models import Currency


class TestCurrencyEnum:
    """Tests for the Currency enumeration."""

    def test_currency_is_string_enum(self):
        """Currency should be a StrEnum so values work as strings."""
        assert Currency.EUR == "EUR"
        assert Currency.USD == "USD"
        assert str(Currency.EUR) == "EUR"

    def test_currency_has_required_values(self):
        """Currency enum must include at least these 10 common currencies."""
        required_currencies = [
            "EUR",
            "USD",
            "GBP",
            "JPY",
            "CHF",
            "CAD",
            "AUD",
            "CNY",
            "INR",
            "MXN",
        ]

        for code in required_currencies:
            assert hasattr(Currency, code), f"Currency.{code} is missing"
            assert Currency[code].value == code

    def test_currency_is_iterable(self):
        """Should be able to iterate over all currency values."""
        currencies = list(Currency)
        assert len(currencies) >= 10
        assert all(isinstance(c, Currency) for c in currencies)
