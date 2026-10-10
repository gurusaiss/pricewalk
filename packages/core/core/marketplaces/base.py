from dataclasses import dataclass
from typing import Protocol

from core.models import Marketplace


@dataclass(frozen=True)
class ParsedProductUrl:
    marketplace: Marketplace
    external_id: str
    canonical_url: str


@dataclass(frozen=True)
class ProductSnapshot:
    title: str | None
    price_paise: int | None
    mrp_paise: int | None
    in_stock: bool
    seller_name: str | None
    deal_label: str | None
    image: str | None


class UnsupportedUrlError(ValueError):
    """Raised when a URL is not a recognizable marketplace product link."""


class UrlResolver(Protocol):
    def __call__(self, url: str) -> str:
        """Resolve a short/redirect URL to its final destination URL."""
        ...
