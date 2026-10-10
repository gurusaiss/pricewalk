# PriceWalk — Claude Code prompts, in order

Put `CLAUDE.md` in the repo root first. Paste one prompt at a time into Claude Code. Move on only when that milestone's tests pass and you've checked it yourself.

---

## M0 — Project setup
```
Read CLAUDE.md. Set up the monorepo exactly as described in "Repo layout".
- docker-compose with Postgres 16, Redis 7, api, worker, web services
- FastAPI app with /health endpoint; arq worker that logs a heartbeat every minute
- Next.js 14 app with Tailwind + shadcn/ui and a placeholder landing page
- packages/core with settings (pydantic-settings), DB session, and Alembic configured
- ruff, mypy, pytest, eslint, prettier configured; a Makefile with dev, test, lint, migrate
- .env.example with every variable
Verify `docker compose up` works and `make test` passes. Then show me how to run it.
```

## M1 — Data model
```
Implement the "Core data model" from CLAUDE.md as SQLAlchemy 2.0 models in packages/core with an Alembic migration.
Money as integer paise, timestamps UTC. Add indexes for (product_id, ts) on price_points and the unique (marketplace, external_id) on products.
Write tests that create a user, a product, tracked items and price points.
```

## M2 — Product link parser
```
In packages/core/marketplaces, build parse_url(url) for Amazon.in, Flipkart and Meesho.
It must handle short links (amzn.in, dl.flipkart.com), mobile URLs, tracking params and affiliate tags, and return (marketplace, external_id, canonical_url).
Unsupported or malformed URLs raise a clear error. Cover 10+ real-world URL shapes per marketplace in tests.
```

## M3 — Page fetcher + snapshot parser
```
Build the fetch + parse layer:
- Async httpx fetcher with realistic headers, timeouts, per-domain rate limiter (Redis token bucket), exponential backoff, and block/CAPTCHA detection that pauses the domain and logs an admin event.
- parse_page(html) -> ProductSnapshot(title, price_paise, mrp_paise, in_stock, seller_name, deal_label, image) for each marketplace.
- Playwright fallback only if httpx HTML lacks the price.
Tests use saved HTML fixtures in tests/fixtures — no live requests in tests.
Also add a CLI: `python -m core.fetch <url>` that prints the snapshot so I can check real pages manually.
```

## M4 — Scheduler + price history
```
Build the tracking loop in services/worker:
- Scheduler runs every minute, finds products due for a check (interval depends on the most demanding active tracked_item: seller 15 min, buyer 60 min), and enqueues fetch jobs.
- Fetch job stores a price_point only when something changed (compare raw_hash) plus a heartbeat point every 6 hours.
- Products nobody tracks anymore stop being polled.
Add tests for the due-calculation and dedup logic. Add an admin endpoint showing queue depth, last success per domain and paused domains.
```

## M5 — Change detection
```
After each new snapshot, compare with the previous one and create change_events for:
price_drop, price_rise, out_of_stock, back_in_stock, deal_start, deal_end.
Ignore price noise under ₹1. Unit-test every event type with before/after pairs.
```

## M6 — Alerts (Telegram first)
```
Build the notifier:
- Telegram bot: user links their account via /start <token> deep link from the web app.
- For each change_event, find users tracking that product and send a formatted alert (product, old → new price, % change, link). Seller alerts say "Competitor <name> …"; buyer alerts say "Price dropped …" and respect target_price.
- Dedupe: never send the same event twice to a user; batch more than 5 events in 10 minutes into one message.
- Daily 9 AM IST summary for sellers.
- Record every send in `alerts`. Design the channel as an interface so WhatsApp and web push can be added later.
Tests with a fake Telegram client.
```

## M7 — Auth + role-based signup
```
Implement auth (email OTP + Google) with JWT in httpOnly cookies.
After first login, show a role picker: "I sell online" (seller) or "I shop online" (buyer). Store it on users.role.
The Next.js app routes and nav depend on role: /seller/* for sellers, /buyer/* for buyers; block cross-role access on both frontend and API.
Allow switching role from settings. Tests for role guards.
```

## M8 — Seller dashboard (main product)
```
Build the seller experience:
- Add "My product" by link, then add competitor links to it (a product group).
- Group view: table of my product vs competitors — current price, stock, deal, last change, cheapest highlighted; price history chart (Recharts) with all lines.
- Alerts feed and settings (channels, quiet hours, which event types).
- "Overpriced / underpriced" badge per group with the gap in ₹ and %.
- Plan limits enforced (free trial: 10 competitor products).
Clean, fast, mobile-friendly UI with shadcn/ui.
```

## M9 — Buyer view (secondary)
```
Build the simple buyer experience:
- Paste a product link → product page with current price, lowest/highest since tracking, history chart, "Set target price" and "Alert me" (Telegram or web push).
- Wishlist page of tracked products.
- Every outbound "Buy" link goes through our redirect endpoint that appends affiliate tags from env vars and logs the click.
```

## M10 — Billing
```
Integrate Razorpay Subscriptions for sellers (UPI autopay + cards).
Plans defined in config (name, monthly price in paise, competitor-product limit, poll interval).
Webhook handler (signature verified, idempotent) updates subscriptions; trial → paid → past_due → cancelled states enforce plan limits.
Billing page in seller settings. Tests with Razorpay webhook fixtures.
```

## M11 — Deploy + monitoring
```
Prepare production deploy: Dockerfiles, Vercel config for web, Railway/Render config for api + worker, managed Postgres/Redis env vars, Alembic migrate on release.
Add Sentry, structured JSON logs, uptime check on /health, and a daily admin Telegram report: products tracked, fetch success rate per domain, alerts sent, blocks detected.
Write DEPLOY.md with exact steps.
```

---

**After each milestone:** run it, test with real product links, commit, then paste the next prompt.
