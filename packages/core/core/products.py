from sqlalchemy.orm import Session

from core.marketplaces import ParsedProductUrl
from core.models import Product


def get_or_create_product(db: Session, parsed: ParsedProductUrl) -> Product:
    product = (
        db.query(Product)
        .filter_by(marketplace=parsed.marketplace, external_id=parsed.external_id)
        .one_or_none()
    )
    if product is None:
        product = Product(
            marketplace=parsed.marketplace,
            external_id=parsed.external_id,
            url=parsed.canonical_url,
        )
        db.add(product)
        db.commit()
    return product
