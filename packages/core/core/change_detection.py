from dataclasses import dataclass

from core.models import ChangeEventType

# Ignore price moves smaller than this - avoids noise from rounding/paise-level
# repricing that isn't a change anyone cares about.
PRICE_NOISE_THRESHOLD_PAISE = 100


@dataclass(frozen=True)
class PriceState:
    price_paise: int | None
    in_stock: bool
    deal_label: str | None


@dataclass(frozen=True)
class DetectedChange:
    type: ChangeEventType
    old_value: str | None
    new_value: str | None


def detect_changes(previous: PriceState, current: PriceState) -> list[DetectedChange]:
    """Compare two consecutive snapshots of the same product and return every
    change_event that should be recorded. Returns [] when nothing crossed a
    meaningful threshold.
    """
    changes: list[DetectedChange] = []

    if previous.price_paise is not None and current.price_paise is not None:
        diff = current.price_paise - previous.price_paise
        if diff <= -PRICE_NOISE_THRESHOLD_PAISE:
            changes.append(
                DetectedChange(
                    ChangeEventType.price_drop,
                    str(previous.price_paise),
                    str(current.price_paise),
                )
            )
        elif diff >= PRICE_NOISE_THRESHOLD_PAISE:
            changes.append(
                DetectedChange(
                    ChangeEventType.price_rise,
                    str(previous.price_paise),
                    str(current.price_paise),
                )
            )

    if previous.in_stock and not current.in_stock:
        changes.append(DetectedChange(ChangeEventType.out_of_stock, "in_stock", "out_of_stock"))
    elif not previous.in_stock and current.in_stock:
        changes.append(DetectedChange(ChangeEventType.back_in_stock, "out_of_stock", "in_stock"))

    had_deal = bool(previous.deal_label)
    has_deal = bool(current.deal_label)
    if not had_deal and has_deal:
        changes.append(DetectedChange(ChangeEventType.deal_start, None, current.deal_label))
    elif had_deal and not has_deal:
        changes.append(DetectedChange(ChangeEventType.deal_end, previous.deal_label, None))

    return changes
