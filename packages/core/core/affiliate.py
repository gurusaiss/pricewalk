from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from core.models import Marketplace
from core.settings import get_settings


def append_affiliate_tag(url: str, marketplace: Marketplace) -> str:
    settings = get_settings()

    tag_param: tuple[str, str] | None = None
    if marketplace == Marketplace.amazon_in and settings.affiliate_tag_amazon:
        tag_param = ("tag", settings.affiliate_tag_amazon)
    elif marketplace == Marketplace.flipkart and settings.affiliate_tag_flipkart:
        tag_param = ("affid", settings.affiliate_tag_flipkart)

    if tag_param is None:
        return url

    parts = urlparse(url)
    query = dict(parse_qsl(parts.query))
    query[tag_param[0]] = tag_param[1]
    return urlunparse(parts._replace(query=urlencode(query)))
