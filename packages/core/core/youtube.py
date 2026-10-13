import json
import re

import httpx

_YOUTUBE_URL_RE = re.compile(
    r"(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)([\w-]{6,})", re.IGNORECASE
)

_TITLE_RE = re.compile(r'"title":"((?:[^"\\]|\\.)*)"')
_DESCRIPTION_RE = re.compile(r'"shortDescription":"((?:[^"\\]|\\.)*)"')


def is_youtube_url(text: str) -> bool:
    return bool(_YOUTUBE_URL_RE.search(text))


def _decode_json_string(raw: str) -> str:
    return json.loads(f'"{raw}"')


async def fetch_youtube_context(
    url: str, client: httpx.AsyncClient | None = None
) -> str | None:
    """Returns "title\\n\\ndescription" for a YouTube video's public page, or
    None if the page couldn't be fetched or parsed. No API key needed - this
    reads the same public page a browser would.

    `client` is injectable so tests can use a mocked transport.
    """
    owns_client = client is None
    http_client = client or httpx.AsyncClient(timeout=15.0, follow_redirects=True)
    try:
        response = await http_client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
    except httpx.HTTPError:
        return None
    finally:
        if owns_client:
            await http_client.aclose()

    html = response.text
    title_match = _TITLE_RE.search(html)
    description_match = _DESCRIPTION_RE.search(html)
    if not title_match and not description_match:
        return None

    title = _decode_json_string(title_match.group(1)) if title_match else ""
    description = _decode_json_string(description_match.group(1)) if description_match else ""
    return f"{title}\n\n{description}".strip()
