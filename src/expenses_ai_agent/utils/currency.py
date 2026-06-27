from decimal import Decimal

import requests
from decouple import config

from expenses_ai_agent.storage.models import Currency

EXCHANGE_RATE_URL = (
    "https://v6.exchangerate-api.com/v6/{API_KEY}/pair/{from_currency}/{to_currency}"
)
TIMEOUT = 3


def convert_currency(
    amount: Decimal,
    *,
    from_currency: Currency,
    to_currency: Currency,
    api_key: str | None = None,
) -> Decimal:
    """Provide up-to-date currency conversion."""

    api_key = config("EXCHANGE_RATE_API_KEY") if api_key is None else api_key
    if from_currency == to_currency:
        return amount

    response = requests.get(
        EXCHANGE_RATE_URL.format(
            API_KEY=api_key,
            from_currency=from_currency,
            to_currency=to_currency,
        ),
        timeout=TIMEOUT,
    )
    # Note:  If pass an invalid/unsupported currency, will get HTTPError/404:
    response.raise_for_status()

    try:
        rate = response.json()["conversion_rate"]
        return (amount * Decimal(str(rate))).quantize(Decimal("0.00"))
    except KeyError as err:
        raise LookupError("Unable to obtain exchange rate.") from err
