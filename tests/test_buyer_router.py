from datetime import UTC, datetime

from core.models import PricePoint, Product, User, UserRole
from tests.helpers import authed_client, make_sqlite_session


def _buyer() -> User:
    return User(email="buyer@example.com", role=UserRole.buyer)


def test_add_to_wishlist() -> None:
    session, engine = make_sqlite_session()
    buyer = _buyer()
    session.add(buyer)
    session.commit()
    try:
        with authed_client(session, buyer) as client:
            response = client.post(
                "/buyer/wishlist",
                json={
                    "product_url": "https://www.amazon.in/dp/B0BUY00001",
                    "target_price_paise": 50000,
                },
            )
            assert response.status_code == 201
            body = response.json()
            assert body["target_price_paise"] == 50000
    finally:
        session.close()
        engine.dispose()


def test_wishlist_shows_lowest_and_highest_price() -> None:
    session, engine = make_sqlite_session()
    buyer = _buyer()
    session.add(buyer)
    session.commit()
    try:
        with authed_client(session, buyer) as client:
            client.post(
                "/buyer/wishlist", json={"product_url": "https://www.amazon.in/dp/B0BUY00002"}
            )

        product = session.query(Product).filter_by(external_id="B0BUY00002").one()
        for price in (9000, 7000, 8500):
            session.add(
                PricePoint(
                    product_id=product.id,
                    ts=datetime.now(UTC),
                    price_paise=price,
                    in_stock=True,
                    raw_hash=str(price),
                )
            )
        session.commit()

        with authed_client(session, buyer) as client:
            wishlist = client.get("/buyer/wishlist").json()
            assert len(wishlist) == 1
            assert wishlist[0]["lowest_price_paise"] == 7000
            assert wishlist[0]["highest_price_paise"] == 9000
    finally:
        session.close()
        engine.dispose()


def test_update_target_price() -> None:
    session, engine = make_sqlite_session()
    buyer = _buyer()
    session.add(buyer)
    session.commit()
    try:
        with authed_client(session, buyer) as client:
            created = client.post(
                "/buyer/wishlist", json={"product_url": "https://www.amazon.in/dp/B0BUY00003"}
            ).json()

            response = client.patch(
                f"/buyer/wishlist/{created['tracked_item_id']}",
                json={"target_price_paise": 12345},
            )
            assert response.status_code == 200
            assert response.json()["target_price_paise"] == 12345
    finally:
        session.close()
        engine.dispose()


def test_remove_wishlist_item() -> None:
    session, engine = make_sqlite_session()
    buyer = _buyer()
    session.add(buyer)
    session.commit()
    try:
        with authed_client(session, buyer) as client:
            created = client.post(
                "/buyer/wishlist", json={"product_url": "https://www.amazon.in/dp/B0BUY00004"}
            ).json()

            delete_resp = client.delete(f"/buyer/wishlist/{created['tracked_item_id']}")
            assert delete_resp.status_code == 200

            wishlist = client.get("/buyer/wishlist").json()
            assert wishlist == []
    finally:
        session.close()
        engine.dispose()


def test_product_detail_includes_history() -> None:
    session, engine = make_sqlite_session()
    buyer = _buyer()
    session.add(buyer)
    session.commit()
    try:
        with authed_client(session, buyer) as client:
            created = client.post(
                "/buyer/wishlist", json={"product_url": "https://www.amazon.in/dp/B0BUY00005"}
            ).json()

        product = session.query(Product).filter_by(external_id="B0BUY00005").one()
        session.add(
            PricePoint(
                product_id=product.id,
                ts=datetime.now(UTC),
                price_paise=4200,
                in_stock=True,
                raw_hash="z",
            )
        )
        session.commit()

        with authed_client(session, buyer) as client:
            detail = client.get(f"/buyer/products/{created['product_id']}").json()
            assert detail["current_price_paise"] == 4200
            assert len(detail["price_history"]) == 1
    finally:
        session.close()
        engine.dispose()


def test_seller_cannot_access_buyer_endpoints() -> None:
    session, engine = make_sqlite_session()
    seller = User(email="seller@example.com", role=UserRole.seller)
    session.add(seller)
    session.commit()
    try:
        with authed_client(session, seller) as client:
            response = client.get("/buyer/wishlist")
            assert response.status_code == 403
    finally:
        session.close()
        engine.dispose()
