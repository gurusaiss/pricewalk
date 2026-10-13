import json
import logging
import re

import httpx

logger = logging.getLogger("core.ai")

_PROMPT = """You help a shopper figure out which products to track prices for.
Given the text below (it may be a free-text description of what someone wants
to buy, or a YouTube video's title/description comparing or reviewing
products), extract the distinct products being discussed or wanted.

Return ONLY a JSON array of short marketplace search queries (product name
plus key distinguishing details, e.g. "Sony WH-1000XM5 headphones"), nothing
else. If there are no identifiable products, return [].

Text:
{text}
"""


def _parse_json_array(raw: str) -> list[str]:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"```$", "", cleaned).strip()
    data = json.loads(cleaned)
    if not isinstance(data, list):
        raise ValueError("expected a JSON array")
    return [str(item).strip() for item in data if str(item).strip()]


class GeminiClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    async def extract_queries(self, text: str) -> list[str]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:generateContent",
                params={"key": self._api_key},
                json={"contents": [{"parts": [{"text": _PROMPT.format(text=text)}]}]},
            )
            response.raise_for_status()
            body = response.json()
        raw = body["candidates"][0]["content"]["parts"][0]["text"]
        return _parse_json_array(raw)


class GroqClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    async def extract_queries(self, text: str) -> list[str]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "messages": [{"role": "user", "content": _PROMPT.format(text=text)}],
                    "temperature": 0,
                },
            )
            response.raise_for_status()
            body = response.json()
        raw = body["choices"][0]["message"]["content"]
        return _parse_json_array(raw)


async def extract_product_queries(
    text: str, gemini: GeminiClient | None, groq: GroqClient | None
) -> list[str]:
    """Tries Gemini first, falls back to Groq. Returns [] if neither is
    configured or both fail - callers should treat that as "couldn't
    identify a product", not as an error.
    """
    for client in (gemini, groq):
        if client is None:
            continue
        try:
            return await client.extract_queries(text)
        except (httpx.HTTPError, KeyError, ValueError, json.JSONDecodeError) as exc:
            logger.warning("smart-tracking: %s failed: %s", type(client).__name__, exc)
    return []
