# Deploying PriceWalk

Everything below uses free tiers: **Vercel** (web), **Render** (api + worker),
**Neon** (Postgres), **Upstash** (Redis). Total cost: ₹0/month at this scale,
and no card is required for any of these four.

> We originally targeted Fly.io, but Fly now requires a payment method on
> file even for free-tier usage. Render's free Web Service plan needs no
> card. The trade-off: Render's free services spin down after ~15 minutes of
> no traffic, so step 8's uptime monitor isn't optional here — it's what
> keeps the API and worker awake. A cold start adds a few seconds of delay
> the first time either service wakes up.

## 0. Accounts you need

Create these first:

| Service | URL | What you'll get | Card needed? |
|---|---|---|---|
| Neon | https://neon.tech | A Postgres connection string | No |
| Upstash | https://upstash.com | A Redis connection string | No |
| Render | https://render.com | Hosting for the API + worker | No |
| Vercel | https://vercel.com | Hosting for the Next.js site | No |
| Telegram | message [@BotFather](https://t.me/BotFather) | A bot token + username (alerts) | No |
| UptimeRobot | https://uptimerobot.com | Keeps Render services awake | No |
| Razorpay | https://dashboard.razorpay.com | Test API keys (billing) | No |

**Login is email + password**, not email + OTP. Every email-sending option we
tried (Brevo, Google Cloud OAuth, Mailjet, SendPulse) gated signup behind a
phone number or card, and Render blocks outbound SMTP on its free tier
entirely (see the note below) — so email-based OTP login isn't practical to
stand up for free right now. The backend still has OTP/email-sending code in
place (untouched, still tested) for whenever a working provider is found;
the frontend just uses `/auth/register` and `/auth/login` for now. Google
sign-in is also **skipped** for the same card-gate reason. Neither blocks
launch — password auth is fully independent and already live.

## 1. Database — Neon

1. On neon.tech, create a project. Choose **Postgres database** only (skip
   Object storage, Functions, AI gateway, Neon Auth — none of those are used;
   our own OTP/JWT auth is already built and tested).
2. Copy the connection string it gives you (it looks like
   `postgresql://user:pass@ep-xxx.neon.tech/dbname?sslmode=require`).
3. Rewrite it for our driver: replace `postgresql://` with
   `postgresql+psycopg://`. This is your `DATABASE_URL`.

## 2. Redis — Upstash

1. Create a Redis database (regional, not global — pick a region close to
   Render's Singapore region, e.g. `ap-southeast-1`).
2. Copy the "Redis URL" (`rediss://...`, note the double `s` — TLS). This is
   your `REDIS_URL`.

## 3. Telegram bot

1. Message [@BotFather](https://t.me/BotFather), run `/newbot`, follow the
   prompts. You get a token (`TELEGRAM_BOT_TOKEN`) and a username
   (`TELEGRAM_BOT_USERNAME`, without the `@`).
2. To get your own chat id for the daily admin report
   (`ADMIN_TELEGRAM_CHAT_ID`): message your new bot once, then open
   `https://api.telegram.org/bot<token>/getUpdates` in a browser and read
   `message.chat.id` from the JSON. (If you get `{"ok":true,"result":[]}`,
   send the bot a fresh message and reload the URL — it only shows updates
   received since the last call.)
3. After deploying the API (step 6), register the webhook so `/start` deep
   links work:
   ```bash
   curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook?url=https://pricewalk-api.onrender.com/telegram/webhook"
   ```

## 4. (Skipped) Email sending for OTP login

Not needed — login uses email + password instead (see the note above). If
you later want OTP login or password-reset emails, three clients already
exist in `packages/core/core/email.py` (`MailjetClient`, `BrevoClient`,
`SmtpClient`) — none usable for free without a phone/card, and Render blocks
outbound SMTP on free services regardless (per Render's own changelog: free
web services no longer allow outbound traffic to SMTP ports). Revisit once
a free, phone-free HTTP email API turns up, or once you're on
a paid Render plan (SMTP works there).

## 5. API + worker — Render

Render deploys both services from the `infra/render.yaml` Blueprint in this
repo (one Dockerfile, two services — `pricewalk-api` and `pricewalk-worker`,
each on the free Web Service plan; the worker runs a tiny health endpoint
alongside the arq loop so Render's free tier, which only offers Web
Services, accepts it).

1. Push this repo to GitHub if you haven't already.
2. On the Render dashboard: **New > Blueprint**, connect the repo, and point
   it at `infra/render.yaml`. Render reads the file and proposes both
   services — confirm.
3. Before the first deploy, set the secret environment variables Render
   left blank (`sync: false` in the blueprint means "prompt me, don't
   commit it") — on **each** service (API and worker need the matching
   values):
   - `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET` (`openssl rand -hex 32`,
     must be identical on both services and on Vercel)
   - `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_USERNAME`, `ADMIN_TELEGRAM_CHAT_ID`
   - `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`,
     `RAZORPAY_PLAN_ID_STARTER`, `RAZORPAY_PLAN_ID_GROWTH` (can be added
     later once you've done step 9)
   - `AFFILIATE_TAG_AMAZON`, `AFFILIATE_TAG_FLIPKART` (optional)
   - `SENTRY_DSN` (optional)
   - On `pricewalk-api` only: `CORS_ORIGINS` — set to your Vercel domain
     once you know it (step 7), e.g. `https://pricewalk.vercel.app`
   - `GOOGLE_CLIENT_ID`, `MAILJET_*`, `BREVO_*`, `SMTP_*` can all stay
     unset — see step 4.
4. Deploy. Render builds the shared Docker image once and starts both
   services. The API's `dockerCommand` runs `alembic upgrade head`
   automatically before `uvicorn` starts, each deploy.
5. Verify: `curl https://pricewalk-api.onrender.com/health` should return
   `{"status": "ok"}` (use your actual service name/domain from the Render
   dashboard).

## 6. Web — Vercel

1. Import the GitHub repo into Vercel.
2. Set **Root Directory** to `apps/web` in the project settings.
3. Add environment variables:
   - `NEXT_PUBLIC_API_URL` = `https://pricewalk-api.onrender.com`
   - `NEXT_PUBLIC_GOOGLE_CLIENT_ID` = (leave unset — Google sign-in is
     skipped)
   - `JWT_SECRET` = **the exact same value** set on Render (middleware.ts
     verifies the same cookie the API issues)
4. Deploy. Vercel builds and hosts the Next.js app with zero other config.
5. Make sure `CORS_ORIGINS` on the Render API service matches this exact
   Vercel domain — update it in the Render dashboard if you set it before
   knowing the final domain (triggers a redeploy automatically).

## 7. Uptime check — required on Render's free tier

Render's free Web Services spin down after ~15 minutes of no inbound
traffic. Pinging both services keeps them awake and gives you an external
alert if the app actually goes down. Add two free
[UptimeRobot](https://uptimerobot.com) monitors:

- Monitor type: HTTP(s), URL: `https://pricewalk-api.onrender.com/health`,
  interval: 5 minutes
- Monitor type: HTTP(s), URL: `https://pricewalk-worker.onrender.com/`,
  interval: 5 minutes

## 8. Razorpay webhook

In the Razorpay dashboard: Settings > Webhooks > Add New Webhook.

- URL: `https://pricewalk-api.onrender.com/webhooks/razorpay`
- Secret: generate one and set it as both the webhook secret in the
  dashboard and `RAZORPAY_WEBHOOK_SECRET` on the Render API service.
- Active events: `subscription.activated`, `subscription.charged`,
  `subscription.pending`, `subscription.halted`, `subscription.cancelled`,
  `subscription.completed`.

Also create the two paid plans (Subscriptions > Plans) and put their ids in
`RAZORPAY_PLAN_ID_STARTER` / `RAZORPAY_PLAN_ID_GROWTH`.

## What's already wired for production

- **Structured JSON logs** (`core/logging_config.py`) on both api and
  worker — tokens/phone/email fields are redacted automatically.
- **Sentry** (`core/sentry.py`) — a no-op until `SENTRY_DSN` is set.
- **DB migrations on deploy** — run automatically as part of the API
  service's start command, before `uvicorn` takes traffic.
- **Daily admin report** (worker cron, 8 AM IST) — products tracked, fetch
  success rate per domain, alerts sent, blocks detected, sent to
  `ADMIN_TELEGRAM_CHAT_ID`.

## Redeploying after code changes

Render redeploys both services automatically on every push to the
connected branch. Vercel does the same for the frontend. No manual command
needed for either.
