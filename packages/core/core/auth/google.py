from typing import Any, Protocol


class GoogleIdTokenVerifier(Protocol):
    def __call__(self, id_token_str: str, client_id: str) -> dict[str, Any]:
        """Return the verified token payload (includes 'email'), or raise ValueError."""
        ...


def verify_google_id_token(id_token_str: str, client_id: str) -> dict[str, Any]:
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token as google_id_token

    payload: dict[str, Any] = google_id_token.verify_oauth2_token(
        id_token_str, google_requests.Request(), client_id
    )
    return payload
