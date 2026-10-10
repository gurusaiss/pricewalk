from core.change_detection import PRICE_NOISE_THRESHOLD_PAISE, PriceState, detect_changes
from core.models import ChangeEventType


def test_price_drop_detected() -> None:
    before = PriceState(price_paise=10000, in_stock=True, deal_label=None)
    after = PriceState(price_paise=9000, in_stock=True, deal_label=None)

    changes = detect_changes(before, after)

    assert len(changes) == 1
    assert changes[0].type == ChangeEventType.price_drop
    assert changes[0].old_value == "10000"
    assert changes[0].new_value == "9000"


def test_price_rise_detected() -> None:
    before = PriceState(price_paise=9000, in_stock=True, deal_label=None)
    after = PriceState(price_paise=10000, in_stock=True, deal_label=None)

    changes = detect_changes(before, after)

    assert len(changes) == 1
    assert changes[0].type == ChangeEventType.price_rise


def test_price_noise_under_threshold_ignored() -> None:
    before = PriceState(price_paise=10000, in_stock=True, deal_label=None)
    after = PriceState(
        price_paise=10000 - (PRICE_NOISE_THRESHOLD_PAISE - 1), in_stock=True, deal_label=None
    )

    assert detect_changes(before, after) == []


def test_price_move_exactly_at_threshold_counts() -> None:
    before = PriceState(price_paise=10000, in_stock=True, deal_label=None)
    after = PriceState(
        price_paise=10000 - PRICE_NOISE_THRESHOLD_PAISE, in_stock=True, deal_label=None
    )

    changes = detect_changes(before, after)

    assert len(changes) == 1
    assert changes[0].type == ChangeEventType.price_drop


def test_out_of_stock_detected() -> None:
    before = PriceState(price_paise=5000, in_stock=True, deal_label=None)
    after = PriceState(price_paise=5000, in_stock=False, deal_label=None)

    changes = detect_changes(before, after)

    assert len(changes) == 1
    assert changes[0].type == ChangeEventType.out_of_stock


def test_back_in_stock_detected() -> None:
    before = PriceState(price_paise=5000, in_stock=False, deal_label=None)
    after = PriceState(price_paise=5000, in_stock=True, deal_label=None)

    changes = detect_changes(before, after)

    assert len(changes) == 1
    assert changes[0].type == ChangeEventType.back_in_stock


def test_deal_start_detected() -> None:
    before = PriceState(price_paise=5000, in_stock=True, deal_label=None)
    after = PriceState(price_paise=5000, in_stock=True, deal_label="Lightning deal")

    changes = detect_changes(before, after)

    assert len(changes) == 1
    assert changes[0].type == ChangeEventType.deal_start
    assert changes[0].new_value == "Lightning deal"


def test_deal_end_detected() -> None:
    before = PriceState(price_paise=5000, in_stock=True, deal_label="Lightning deal")
    after = PriceState(price_paise=5000, in_stock=True, deal_label=None)

    changes = detect_changes(before, after)

    assert len(changes) == 1
    assert changes[0].type == ChangeEventType.deal_end
    assert changes[0].old_value == "Lightning deal"


def test_no_change_yields_no_events() -> None:
    state = PriceState(price_paise=5000, in_stock=True, deal_label=None)
    assert detect_changes(state, state) == []


def test_multiple_simultaneous_changes_all_detected() -> None:
    before = PriceState(price_paise=10000, in_stock=True, deal_label=None)
    after = PriceState(price_paise=7000, in_stock=False, deal_label="Flash sale")

    changes = detect_changes(before, after)
    types = {c.type for c in changes}

    assert types == {
        ChangeEventType.price_drop,
        ChangeEventType.out_of_stock,
        ChangeEventType.deal_start,
    }


def test_price_unknown_on_either_side_skips_price_comparison() -> None:
    before = PriceState(price_paise=None, in_stock=True, deal_label=None)
    after = PriceState(price_paise=9000, in_stock=True, deal_label=None)

    assert detect_changes(before, after) == []
