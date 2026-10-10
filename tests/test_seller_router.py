from datetime import UTC, datetime

from core.models import PricePoint, Product, User, UserRole
from tests.helpers import authed_client, make_sqlite_session


def _seller() -> User:
    return User(email="seller@example.com", role=UserRole.seller, plan="trial")


def test_create_group_creates_own_tracked_item() -> None:
    session, engine = make_sqlite_session()
    seller = _seller()
    session.add(seller)
    session.commit()
    try:
        with authed_client(session, seller) as client:
            response = client.post(
                "/seller/groups",
                json={"name": "My Widget", "product_url": "https://www.amazon.in/dp/B0WIDGET01"},
            )
            assert response.status_code == 201
            body = response.json()
            assert body["name"] == "My Widget"
            assert len(body["members"]) == 1
            assert body["members"][0]["kind"] == "own"
            assert body["status"] is None  # no price data yet
    finally:
        session.close()
        engine.dispose()


def test_add_competitor_and_compute_gap() -> None:
    session, engine = make_sqlite_session()
    seller = _seller()
    session.add(seller)
    session.commit()
    try:
        with authed_client(session, seller) as client:
            group_resp = client.post(
                "/seller/groups",
                json={"name": "My Widget", "product_url": "https://www.amazon.in/dp/B0WIDGET02"},
            )
            group_id = group_resp.json()["id"]

            competitor_resp = client.post(
                f"/seller/groups/{group_id}/competitors",
                json={"product_url": "https://www.flipkart.com/p/itmCOMPETITOR1"},
            )
            assert competitor_resp.status_code == 201
            body = competitor_resp.json()
            assert len(body["members"]) == 2

        # Seed price points: own = 11000 paise, competitor = 10000 paise.
        own_product = session.query(Product).filter_by(external_id="B0WIDGET02").one()
        competitor_product = session.query(Product).filter_by(external_id="itmCOMPETITOR1").one()
        session.add(
            PricePoint(
                product_id=own_product.id,
                ts=datetime.now(UTC),
                price_paise=11000,
                in_stock=True,
                raw_hash="a",
            )
        )
        session.add(
            PricePoint(
                product_id=competitor_product.id,
                ts=datetime.now(UTC),
                price_paise=10000,
                in_stock=True,
                raw_hash="b",
            )
        )
        session.commit()

        with authed_client(session, seller) as client:
            group_list = client.get("/seller/groups").json()
            group = group_list[0]
            assert group["status"] == "overpriced"
            assert group["gap_paise"] == 1000
            cheapest = [m for m in group["members"] if m["is_cheapest"]]
            assert len(cheapest) == 1
            assert cheapest[0]["kind"] == "competitor"
    finally:
        session.close()
        engine.dispose()


def test_competitor_limit_enforced() -> None:
    session, engine = make_sqlite_session()
    seller = _seller()
    session.add(seller)
    session.commit()
    try:
        with authed_client(session, seller) as client:
            group_resp = client.post(
                "/seller/groups",
                json={"name": "My Widget", "product_url": "https://www.amazon.in/dp/B0WIDGET03"},
            )
            group_id = group_resp.json()["id"]

            for i in range(10):
                response = client.post(
                    f"/seller/groups/{group_id}/competitors",
                    json={"product_url": f"https://www.flipkart.com/p/itmLIMIT{i:03d}"},
                )
                assert response.status_code == 201

            over_limit_response = client.post(
                f"/seller/groups/{group_id}/competitors",
                json={"product_url": "https://www.flipkart.com/p/itmLIMITOVER"},
            )
            assert over_limit_response.status_code == 402
    finally:
        session.close()
        engine.dispose()


def test_get_group_404_for_other_users_group() -> None:
    session, engine = make_sqlite_session()
    seller = _seller()
    other_seller = User(email="other@example.com", role=UserRole.seller, plan="trial")
    session.add_all([seller, other_seller])
    session.commit()
    try:
        with authed_client(session, seller) as client:
            group_resp = client.post(
                "/seller/groups",
                json={"name": "My Widget", "product_url": "https://www.amazon.in/dp/B0WIDGET04"},
            )
            group_id = group_resp.json()["id"]

        with authed_client(session, other_seller) as client:
            response = client.get(f"/seller/groups/{group_id}")
            assert response.status_code == 404
    finally:
        session.close()
        engine.dispose()


def test_remove_group_item_soft_deletes() -> None:
    session, engine = make_sqlite_session()
    seller = _seller()
    session.add(seller)
    session.commit()
    try:
        with authed_client(session, seller) as client:
            group_resp = client.post(
                "/seller/groups",
                json={"name": "My Widget", "product_url": "https://www.amazon.in/dp/B0WIDGET05"},
            )
            group = group_resp.json()
            item_id = group["members"][0]["tracked_item_id"]

            delete_resp = client.delete(f"/seller/groups/{group['id']}/items/{item_id}")
            assert delete_resp.status_code == 200

            refreshed = client.get(f"/seller/groups/{group['id']}").json()
            assert refreshed["members"] == []
    finally:
        session.close()
        engine.dispose()


def test_price_history_returns_points() -> None:
    session, engine = make_sqlite_session()
    seller = _seller()
    session.add(seller)
    session.commit()
    try:
        with authed_client(session, seller) as client:
            group_resp = client.post(
                "/seller/groups",
                json={"name": "My Widget", "product_url": "https://www.amazon.in/dp/B0WIDGET06"},
            )
            group_id = group_resp.json()["id"]

        product = session.query(Product).filter_by(external_id="B0WIDGET06").one()
        session.add(
            PricePoint(
                product_id=product.id,
                ts=datetime.now(UTC),
                price_paise=5000,
                in_stock=True,
                raw_hash="x",
            )
        )
        session.commit()

        with authed_client(session, seller) as client:
            history = client.get(f"/seller/groups/{group_id}/price-history").json()
            assert len(history) == 1
            assert history[0]["points"][0]["price_paise"] == 5000
    finally:
        session.close()
        engine.dispose()


def test_alert_settings_round_trip() -> None:
    session, engine = make_sqlite_session()
    seller = _seller()
    session.add(seller)
    session.commit()
    try:
        with authed_client(session, seller) as client:
            response = client.patch(
                "/seller/alert-settings",
                json={
                    "quiet_hours_start": 22,
                    "quiet_hours_end": 7,
                    "alert_event_types": ["price_drop"],
                },
            )
            assert response.status_code == 200
            body = response.json()
            assert body["quiet_hours_start"] == 22
            assert body["alert_event_types"] == ["price_drop"]

            fetched = client.get("/seller/alert-settings").json()
            assert fetched["quiet_hours_end"] == 7
    finally:
        session.close()
        engine.dispose()


def test_buyer_cannot_access_seller_endpoints() -> None:
    session, engine = make_sqlite_session()
    buyer = User(email="buyer@example.com", role=UserRole.buyer)
    session.add(buyer)
    session.commit()
    try:
        with authed_client(session, buyer) as client:
            response = client.get("/seller/groups")
            assert response.status_code == 403
    finally:
        session.close()
        engine.dispose()
