import logging
from typing import Any

from core.db import SessionLocal
from core.scheduling import due_products

logger = logging.getLogger("worker.scheduler")


async def enqueue_due_products(ctx: dict[str, Any]) -> None:
    redis = ctx["redis"]
    with SessionLocal() as session:
        products = due_products(session)

    for product in products:
        await redis.enqueue_job("fetch_product", str(product.id))

    if products:
        logger.info("enqueued %d due product(s) for a price check", len(products))
