from dataclasses import dataclass
from typing import Protocol

from core.models import Marketplace


@dataclass(frozen=True)
class ParsedProductUrl:
    marketplace: Marketplace
    external_id: str
    canonical_url: str


class UnsupportedUrlError(ValueError):
    """Raised when a URL is not a recognizable marketplace product link."""


class UrlResolver(Protocol):
    def __call__(self, url: str) -> str:
        """Resolve a short/redirect URL to its final destination URL."""
        ...
