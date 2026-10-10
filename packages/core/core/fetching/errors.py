class BlockedError(Exception):
    """Raised when a response looks like a CAPTCHA/block page."""

    def __init__(self, domain: str, reason: str) -> None:
        super().__init__(f"Blocked by {domain}: {reason}")
        self.domain = domain
        self.reason = reason


class DomainPausedError(Exception):
    """Raised when a domain is currently paused after a prior block/CAPTCHA."""

    def __init__(self, domain: str) -> None:
        super().__init__(f"{domain} is paused after a previous block/CAPTCHA detection")
        self.domain = domain
