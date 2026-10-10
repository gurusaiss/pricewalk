import re

_NUMBER_RE = re.compile(r"[\d,]+(?:\.\d+)?")


def parse_price_to_paise(text: str | float | int | None) -> int | None:
    """Parse a rupee amount ("₹1,234.50", "1234.5", 1234.5) into integer paise."""
    if text is None:
        return None
    if isinstance(text, (int, float)):
        return round(float(text) * 100)

    cleaned = text.replace("\xa0", " ").strip()
    match = _NUMBER_RE.search(cleaned)
    if match is None:
        return None

    value = match.group(0).replace(",", "")
    try:
        rupees = float(value)
    except ValueError:
        return None
    return round(rupees * 100)
