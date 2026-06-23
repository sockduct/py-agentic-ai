from decimal import Decimal

import requests
from decouple import config

from expenses_ai_agent.storage.models import Currency

EXCHANGE_RATE_API_KEY = config("EXCHANGE_RATE_API_KEY")
EXCHANGE_RATE_URL = (
    "https://v6.exchangerate-api.com/v6/{API_KEY}/pair/{from_currency}/{to_currency}"
)
TIMEOUT = 3


def convert_currency(
    amount: Decimal, from_currency: str, to_currency: str, *, warn: bool = False
) -> Decimal:
    """Provide up-to-date currency conversion."""

    if warn and to_currency not in Currency:
        print(f"Warning: {to_currency} not a supported currency.")

    if from_currency == to_currency:
        return amount

    response = requests.get(
        EXCHANGE_RATE_URL.format(
            API_KEY=EXCHANGE_RATE_API_KEY,
            from_currency=from_currency,
            to_currency=to_currency,
        ),
        timeout=TIMEOUT,
    )
    # Note:  If pass an invalid/unsupported currency, will get HTTPError/404:
    response.raise_for_status()

    if rate := response.json().get("conversion_rate"):
        return (amount * Decimal(str(rate))).quantize(Decimal("0.00"))
    else:
        raise LookupError("Unable to obtain exchange rate.")
