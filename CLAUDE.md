# CLAUDE.md — PriceWalk (working name)

## What we are building
A price-tracking platform for Indian e-commerce with **two user roles**, chosen at signup:

- **Seller** (main business + marketing focus): tracks competitor products on Amazon.in, Flipkart and Meesho and gets alerts within minutes when a competitor changes price, goes out of stock, or starts a deal. Pays a monthly subscription (UPI via Razorpay).
- **Buyer** (secondary, free): tracks products they want to buy and gets a price-drop alert plus price history.

After signup the user picks "I'm a Seller" or "I'm a Buyer". Features, navigation and pages depend on that role. Seller features take priority in every decision.

## Hard rules
1. **No logins on marketplaces.** Never automate logging into Amazon/Flipkart/Meesho/Swiggy/Zomato or store anyone's marketplace credentials. Read public product pages only.
2. **Polite scraping.** Default poll interval per product: 15 min (seller plans), 60 min (buyers). Never faster than 5 min per product. Global rate limit per domain. Respect failures with exponential backoff. On CAPTCHA/block: pause that domain, log it, alert admin — never hammer.
3. **Never store passwords in plain text**; never log tokens, phone numbers or emails at INFO level.
4. Price history starts the day we begin tracking — never fabricate or backfill history.
5. Store all money as integer paise. Store all times in UTC; display in IST.

## Tech stack
- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0 + Alembic, Pydantic v2
- **Jobs:** Redis + `arq` worker (scheduler enqueues due products; workers fetch, parse, detect changes)
- **Fetching/parsing:** `httpx` (async) + `selectolax`; Playwright only as fallback for pages that need JS
- **Database:** PostgreSQL (TimescaleDB extension optional for `price_points`)
- **Frontend:** Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui, charts with Recharts
- **Auth:** email + OTP or Google sign-in (JWT, httpOnly cookies)
- **Alerts:** Telegram bot first; WhatsApp Cloud API later; web push (FCM) for buyers
- **Payments:** Razorpay Subscriptions (UPI autopay)
- **Deploy:** frontend on Vercel; API + worker on Railway/Render; managed Postgres + Redis
- **Local dev:** `docker compose up` brings up Postgres, Redis, API, worker, web

## Repo layout
```
/apps/web            Next.js frontend
/services/api        FastAPI app (routers, schemas, auth, billing)
/services/worker     arq worker: scheduler, fetchers, parsers, change detection, notifiers
/packages/core       shared Python: models, db session, marketplace parsers, settings
/infra               docker-compose, Dockerfiles, deploy configs
/tests               pytest (parsers use saved HTML fixtures, never live sites)
```

## Core data model
- `users` (id, email, phone, role: seller|buyer, plan, created_at)
- `products` (id, marketplace, external_id, url, title, image, brand, category) — unique on (marketplace, external_id)
- `tracked_items` (id, user_id, product_id, kind: own|competitor|wishlist, group_id, target_price, active)
- `product_groups` (seller only: "my product X vs its competitors")
- `price_points` (product_id, ts, price_paise, mrp_paise, in_stock, seller_name, deal_label, raw_hash)
- `change_events` (product_id, ts, type: price_drop|price_rise|out_of_stock|back_in_stock|deal_start|deal_end, old, new)
- `alerts` (id, user_id, change_event_id, channel, sent_at, status)
- `subscriptions` (user_id, razorpay_sub_id, plan, status, current_period_end)

## Marketplace parsers
One module per marketplace in `packages/core/marketplaces/` implementing:
`parse_url(url) -> (marketplace, external_id)` and `parse_page(html) -> ProductSnapshot`.
Every parser has fixture-based tests in `/tests/fixtures/<marketplace>/`. When a parser breaks, add the new HTML as a fixture before fixing it.

## Conventions
- Type hints everywhere; `ruff` + `mypy` for Python, `eslint` + `prettier` for TS.
- Small, focused modules; business logic out of route handlers.
- Every feature ships with tests. Run `pytest` and `npm run lint` before declaring done.
- Config via environment variables (`.env.example` kept up to date). No secrets in git.
- Commit in small steps with clear messages.

## Current milestone
See `PROMPTS.md`. Work one milestone at a time; don't start the next until tests pass.
