import httpx

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
}


def resolve_redirect(url: str, timeout: float = 10.0) -> str:
    """Follow redirects on a short/deep link and return the final URL.

    Used only for short-link domains (amzn.in, dl.flipkart.com, ...) whose path
    doesn't itself contain the product id. Never called in tests - callers pass
    a stub resolver instead so parser tests make no network requests.
    """
    with httpx.Client(follow_redirects=True, timeout=timeout, headers=_HEADERS) as client:
        response = client.get(url)
        return str(response.url)
