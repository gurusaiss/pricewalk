import httpx


class BrevoClient:
    """Thin wrapper over Brevo's transactional email API (free tier, no domain
    verification needed to send to any recipient).
    """

    def __init__(self, api_key: str, sender_email: str, sender_name: str = "PriceWalk") -> None:
        self._api_key = api_key
        self._sender = {"email": sender_email, "name": sender_name}

    async def send_email(self, to_email: str, subject: str, text: str) -> bool:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={"api-key": self._api_key, "content-type": "application/json"},
                json={
                    "sender": self._sender,
                    "to": [{"email": to_email}],
                    "subject": subject,
                    "textContent": text,
                },
            )
        return response.status_code in (200, 201)
