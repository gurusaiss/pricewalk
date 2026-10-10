from core.models import ChangeEvent, ChangeEventType, Product

_EVENT_VERBS = {
    ChangeEventType.price_drop: "price dropped",
    ChangeEventType.price_rise: "price increased",
    ChangeEventType.out_of_stock: "went out of stock",
    ChangeEventType.back_in_stock: "is back in stock",
    ChangeEventType.deal_start: "started a deal",
    ChangeEventType.deal_end: "deal ended",
}


def _rupees(paise: str | None) -> str:
    if paise is None:
        return "?"
    try:
        value = int(paise) / 100
    except ValueError:
        return "?"
    return f"₹{value:,.2f}"


def _pct_change(old: str | None, new: str | None) -> str | None:
    if old is None or new is None:
        return None
    try:
        old_value = float(old)
        new_value = float(new)
    except ValueError:
        return None
    if old_value == 0:
        return None
    pct = (new_value - old_value) / old_value * 100
    return f"{pct:+.1f}%"


def format_seller_alert(product: Product, event: ChangeEvent) -> str:
    title = product.title or product.external_id
    verb = _EVENT_VERBS[event.type]
    lines = [f"Competitor {title} {verb}."]

    if event.type in (ChangeEventType.price_drop, ChangeEventType.price_rise):
        line = f"{_rupees(event.old_value)} -> {_rupees(event.new_value)}"
        pct = _pct_change(event.old_value, event.new_value)
        if pct:
            line += f" ({pct})"
        lines.append(line)

    lines.append(product.url)
    return "\n".join(lines)


def format_buyer_alert(product: Product, event: ChangeEvent) -> str:
    title = product.title or product.external_id

    if event.type == ChangeEventType.price_drop:
        line = (
            f"Price dropped for {title}: {_rupees(event.old_value)} -> {_rupees(event.new_value)}"
        )
        pct = _pct_change(event.old_value, event.new_value)
        if pct:
            line += f" ({pct})"
    elif event.type == ChangeEventType.back_in_stock:
        line = f"{title} is back in stock!"
    else:
        line = f"{title} {_EVENT_VERBS[event.type]}."

    return f"{line}\n{product.url}"
