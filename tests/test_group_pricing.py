from core.group_pricing import compute_price_gap


def test_overpriced_when_own_price_higher() -> None:
    gap = compute_price_gap(own_price_paise=11000, cheapest_competitor_price_paise=10000)
    assert gap.gap_paise == 1000
    assert gap.gap_percent == 10.0
    assert gap.status == "overpriced"


def test_underpriced_when_own_price_lower() -> None:
    gap = compute_price_gap(own_price_paise=9000, cheapest_competitor_price_paise=10000)
    assert gap.gap_paise == -1000
    assert gap.status == "underpriced"


def test_match_when_equal() -> None:
    gap = compute_price_gap(own_price_paise=10000, cheapest_competitor_price_paise=10000)
    assert gap.gap_paise == 0
    assert gap.status == "match"


def test_none_when_either_price_missing() -> None:
    assert compute_price_gap(None, 10000).status is None
    assert compute_price_gap(10000, None).status is None
    assert compute_price_gap(None, None).status is None
