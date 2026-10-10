from dataclasses import dataclass


@dataclass(frozen=True)
class PriceGap:
    gap_paise: int | None
    gap_percent: float | None
    status: str | None  # "overpriced" | "underpriced" | "match" | None


def compute_price_gap(
    own_price_paise: int | None, cheapest_competitor_price_paise: int | None
) -> PriceGap:
    """Compare a seller's own product price against the cheapest competitor.

    Positive gap = priced above the cheapest competitor (overpriced);
    negative = priced below it (underpriced).
    """
    if own_price_paise is None or cheapest_competitor_price_paise is None:
        return PriceGap(None, None, None)

    gap = own_price_paise - cheapest_competitor_price_paise
    percent = (
        round(gap / cheapest_competitor_price_paise * 100, 1)
        if cheapest_competitor_price_paise
        else None
    )

    if gap > 0:
        status = "overpriced"
    elif gap < 0:
        status = "underpriced"
    else:
        status = "match"

    return PriceGap(gap, percent, status)
