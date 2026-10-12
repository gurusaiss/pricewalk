import asyncio
import smtplib
from email.message import EmailMessage

import httpx


class SmtpClient:
    """Sends mail through any SMTP server (e.g. Gmail's smtp.gmail.com:465
    with an app password) — a free alternative to Brevo when its signup
    requires phone verification you can't complete.
    """

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        sender_email: str,
        sender_name: str = "PriceWalk",
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._sender = f"{sender_name} <{sender_email}>"

    def _send_sync(self, to_email: str, subject: str, text: str) -> bool:
        message = EmailMessage()
        message["From"] = self._sender
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(text)

        try:
            with smtplib.SMTP_SSL(self._host, self._port, timeout=10) as server:
                server.login(self._username, self._password)
                server.send_message(message)
            return True
        except smtplib.SMTPException:
            return False

    async def send_email(self, to_email: str, subject: str, text: str) -> bool:
        return await asyncio.to_thread(self._send_sync, to_email, subject, text)


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
