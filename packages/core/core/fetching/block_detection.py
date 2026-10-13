_BLOCK_MARKERS = (
    "captcha",
    "robot check",
    "enter the characters you see below",
    "access denied",
    "unusual traffic",
    "automated access",
    "pardon our interruption",
    "bm-verify",  # Akamai Bot Manager's silent JS interstitial challenge
)


def looks_blocked(status_code: int, html: str) -> str | None:
    """Return a reason string if the response looks like a CAPTCHA/block page.

    403/429 are near-universally bot-detection responses, so they're treated as
    a block outright. 503 is ambiguous (transient overload vs. a block page) so
    it's left to the generic retry-on-5xx path unless the body itself contains
    a block marker.
    """
    if status_code in (403, 429):
        return f"http status {status_code}"

    lowered = html.lower()
    for marker in _BLOCK_MARKERS:
        if marker in lowered:
            return f"page contains block marker: {marker!r}"
    return None
