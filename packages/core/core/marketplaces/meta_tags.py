from selectolax.lexbor import LexborHTMLParser as HTMLParser


def get_meta_content(tree: HTMLParser, property_or_name: str) -> str | None:
    for attr in ("property", "name"):
        node = tree.css_first(f'meta[{attr}="{property_or_name}"]')
        if node is not None:
            content = node.attributes.get("content")
            if content:
                return content
    return None
