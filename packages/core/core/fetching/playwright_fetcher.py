async def fetch_with_playwright(url: str, timeout_ms: int = 20_000) -> str:
    """Render a page with a headless browser for JS-heavy pages httpx can't see.

    Only used as a fallback when the plain HTML fetch is missing a price.
    Imports playwright lazily so it isn't a hard requirement for code paths
    (and tests) that never need it; run `playwright install chromium` once
    before using this.
    """
    from playwright.async_api import async_playwright

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        try:
            page = await browser.new_page()
            await page.goto(url, timeout=timeout_ms, wait_until="networkidle")
            return await page.content()
        finally:
            await browser.close()
