from typing import Protocol


class AlertChannelClient(Protocol):
    """Interface every alert channel (Telegram, WhatsApp, web push) implements,
    so the notifier doesn't care which channel it's sending through.
    """

    async def send(self, chat_id: str, message: str) -> bool:
        """Send a message; return True on success."""
        ...
