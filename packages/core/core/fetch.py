"""CLI: `python -m core.fetch <url>` - fetch a real product page and print its snapshot."""

import asyncio
import dataclasses
import json
import sys

from redis.asyncio import Redis

from core.fetching import fetch_snapshot
from core.fetching.playwright_fetcher import fetch_with_playwright
from core.settings import get_settings


async def _main(url: str) -> None:
    settings = get_settings()
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        parsed, snapshot = await fetch_snapshot(url, redis, playwright_fetch=fetch_with_playwright)
    finally:
        await redis.aclose()

    print(
        json.dumps(
            {
                "marketplace": parsed.marketplace.value,
                "external_id": parsed.external_id,
                "canonical_url": parsed.canonical_url,
                **dataclasses.asdict(snapshot),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: python -m core.fetch <url>", file=sys.stderr)
        raise SystemExit(2)
    asyncio.run(_main(sys.argv[1]))


if __name__ == "__main__":
    main()
