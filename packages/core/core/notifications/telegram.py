from typing import Any

import httpx


class TelegramClient:
    """Thin wrapper over the Telegram Bot API. Implements AlertChannelClient."""

    def __init__(self, bot_token: str, timeout: float = 10.0) -> None:
        self._base_url = f"https://api.telegram.org/bot{bot_token}"
        self._timeout = timeout

    async def send(self, chat_id: str, message: str) -> bool:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": False,
                },
            )
        return response.status_code == 200

    async def get_updates(self, offset: int | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if offset is not None:
            params["offset"] = offset
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(f"{self._base_url}/getUpdates", params=params)
        response.raise_for_status()
        result: list[dict[str, Any]] = response.json().get("result", [])
        return result
