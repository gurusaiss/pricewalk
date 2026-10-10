from urllib.parse import urlsplit

from .base import UnsupportedUrlError


def normalize(url: str) -> str:
    url = url.strip()
    if not url:
        raise UnsupportedUrlError("Empty URL")
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


def split_host_path(url: str) -> tuple[str, str]:
    parts = urlsplit(url)
    host = parts.netloc.split(":")[0].lower()
    return host, parts.path
