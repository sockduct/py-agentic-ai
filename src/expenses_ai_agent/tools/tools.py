"""
Create two module-level dicts following the OpenAI tool schema format (see Helpful References)

CURRENCY_CONVERSION_TOOL — for convert_currency; amount, from_currency, to_currency are all required
DATETIME_FORMATTER_TOOL — for format_datetime; datetime_str is required, timezone_str is optional
"""

CURRENCY_CONVERSION_TOOL: dict = {
    "type": "function",
    "name": "convert_currency",
    "description": "Provide up-to-date currency conversion.",
    "strict": True,
    "parameters": {
        "type": "object",
        "properties": {
            "amount": {
                "type": "float",
                "description": "Numeric value of current currency.",
            },
            "from_currency": {
                "type": "string",
                "description": "Currency the amount is currently in e.g. USD",
            },
            "to_currency": {
                "type": "string",
                "description": "Currency to convert to e.g. EUR",
            },
        },
        "required": ["amount", "from_currency", "to_currency"],
        "additionalProperties": False,
    },
}

DATETIME_FORMATTER_TOOL: dict = {
    "type": "function",
    "name": "format_datetime",
    "description": "Parse datetime string from ISO format including support for specified timezone",
    "strict": True,
    "parameters": {
        "type": "object",
        "properties": {
            "datetime_str": {
                "type": "string",
                "description": "Date and time string in ISO 8601 format.",
            },
            "timezone_str": {
                "type": "string",
                "description": "Optional IANA Time Zone string for datetime_str.",
            },
        },
        "required": ["datetime_str"],
        "additionalProperties": False,
    },
}
