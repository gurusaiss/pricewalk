from typing import Any

import httpx

_BASE_URL = "https://api.razorpay.com/v1"


class RazorpayClient:
    """Thin wrapper over the Razorpay Subscriptions REST API."""

    def __init__(self, key_id: str, key_secret: str) -> None:
        self._auth = (key_id, key_secret)

    async def create_subscription(
        self,
        plan_id: str,
        notes: dict[str, str] | None = None,
        total_count: int = 120,
    ) -> dict[str, Any]:
        """Create a subscription and return it (includes `id` and a hosted
        `short_url` the customer completes UPI autopay/card authorization on).
        """
        async with httpx.AsyncClient(timeout=15.0, auth=self._auth) as client:
            response = await client.post(
                f"{_BASE_URL}/subscriptions",
                json={
                    "plan_id": plan_id,
                    "customer_notify": 1,
                    "total_count": total_count,
                    "notes": notes or {},
                },
            )
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result
