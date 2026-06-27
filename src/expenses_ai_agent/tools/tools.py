"""
Create two module-level dicts following the OpenAI tool schema format (see Helpful References)

CURRENCY_CONVERSION_TOOL — for convert_currency; amount, from_currency, to_currency are all required
DATETIME_FORMATTER_TOOL — for format_datetime; datetime_str is required, timezone_str is optional
"""

from openai.types.responses import FunctionToolParam

CURRENCY_CONVERSION_TOOL: FunctionToolParam = {
    "type": "function",
    "name": "convert_currency",
    "description": "Provide up-to-date currency conversion.",
    "strict": True,
    "parameters": {
        "type": "object",
        "properties": {
            "amount": {
                "type": "number",
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

DATETIME_FORMATTER_TOOL: FunctionToolParam = {
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
                "type": ["string", "null"],
                "description": "Optional IANA Time Zone string for datetime_str.",
            },
        },
        "required": ["datetime_str", "timezone_str"],
        "additionalProperties": False,
    },
}
