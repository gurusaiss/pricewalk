import pytest

from core.ai import extract_product_queries


class FakeClient:
    def __init__(self, result: list[str] | None = None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.calls: list[str] = []

    async def extract_queries(self, text: str) -> list[str]:
        self.calls.append(text)
        if self.error:
            raise self.error
        return self.result or []


@pytest.mark.asyncio
async def test_uses_gemini_when_it_succeeds() -> None:
    gemini = FakeClient(result=["Sony WH-1000XM5 headphones"])
    groq = FakeClient(result=["should not be used"])

    queries = await extract_product_queries("great noise cancelling headphones", gemini, groq)

    assert queries == ["Sony WH-1000XM5 headphones"]
    assert groq.calls == []


@pytest.mark.asyncio
async def test_falls_back_to_groq_when_gemini_fails() -> None:
    gemini = FakeClient(error=ValueError("bad response"))
    groq = FakeClient(result=["budget wireless earbuds"])

    queries = await extract_product_queries("cheap earbuds under 2000", gemini, groq)

    assert queries == ["budget wireless earbuds"]


@pytest.mark.asyncio
async def test_returns_empty_list_when_both_fail() -> None:
    gemini = FakeClient(error=ValueError("bad"))
    groq = FakeClient(error=ValueError("also bad"))

    queries = await extract_product_queries("some text", gemini, groq)

    assert queries == []


@pytest.mark.asyncio
async def test_returns_empty_list_when_neither_configured() -> None:
    queries = await extract_product_queries("some text", None, None)

    assert queries == []
