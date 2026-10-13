import httpx
import pytest

from core.youtube import fetch_youtube_context, is_youtube_url


def test_is_youtube_url_matches_common_forms() -> None:
    assert is_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert is_youtube_url("https://youtu.be/dQw4w9WgXcQ")
    assert is_youtube_url("https://www.youtube.com/shorts/dQw4w9WgXcQ")


def test_is_youtube_url_rejects_other_urls() -> None:
    assert not is_youtube_url("https://www.amazon.in/dp/B08N5WRWNW")
    assert not is_youtube_url("budget wireless earbuds under 2000")


def _mock_client(html: str, status_code: int = 200) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, text=html)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_extracts_title_and_description() -> None:
    html = (
        '<script>var x = {"title":"Top 5 Budget Earbuds 2026",'
        '"shortDescription":"Comparing the best picks under 2000 rupees."};</script>'
    )
    client = _mock_client(html)
    try:
        context = await fetch_youtube_context("https://www.youtube.com/watch?v=abc123", client)
    finally:
        await client.aclose()

    assert context == "Top 5 Budget Earbuds 2026\n\nComparing the best picks under 2000 rupees."


@pytest.mark.asyncio
async def test_returns_none_when_page_has_no_matching_fields() -> None:
    client = _mock_client("<html><body>nothing here</body></html>")
    try:
        context = await fetch_youtube_context("https://www.youtube.com/watch?v=abc123", client)
    finally:
        await client.aclose()

    assert context is None


@pytest.mark.asyncio
async def test_returns_none_on_http_error() -> None:
    client = _mock_client("not found", status_code=404)
    try:
        context = await fetch_youtube_context("https://www.youtube.com/watch?v=abc123", client)
    finally:
        await client.aclose()

    assert context is None
