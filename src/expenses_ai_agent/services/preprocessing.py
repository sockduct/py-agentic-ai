import re
from dataclasses import dataclass, field

MIN_LENGTH = 3
MAX_LENGTH = 500

XSS_PATTERNS = ("<script", "javascript:", "onerror=", "onload=")

CURRENCY_SYMBOLS = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY"}

AMOUNT_PATTERN = re.compile(r"\d+([.,]\d+)?")


@dataclass
class PreprocessingResult:
    text: str
    is_valid: bool
    warnings: list[str] = field(default_factory=list)
    error: str | None = None


class InputPreprocessor:
    def preprocess(self, text: str) -> PreprocessingResult:
        cleaned = text.strip()

        if len(cleaned) < MIN_LENGTH:
            return PreprocessingResult(
                cleaned,
                is_valid=False,
                error=f"Input too short (minimum {MIN_LENGTH} characters)",
            )
        if len(cleaned) > MAX_LENGTH:
            return PreprocessingResult(
                cleaned,
                is_valid=False,
                error=f"Input too long (maximum {MAX_LENGTH} characters)",
            )
        if any(pattern in cleaned.lower() for pattern in XSS_PATTERNS):
            return PreprocessingResult(
                cleaned, is_valid=False, error="Invalid input detected"
            )

        for symbol, code in CURRENCY_SYMBOLS.items():
            cleaned = cleaned.replace(symbol, code)

        warnings: list[str] = []
        if AMOUNT_PATTERN.search(cleaned) is None:
            warnings.append("No amount detected — the AI will try to infer it")

        return PreprocessingResult(cleaned, is_valid=True, warnings=warnings)
