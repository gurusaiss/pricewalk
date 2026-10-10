# Deploying PriceWalk

Everything below uses free tiers: **Vercel** (web), **Fly.io** (api + worker),
**Neon** (Postgres), **Upstash** (Redis). Total cost: ₹0/month at this scale.

## 0. Accounts you need

Create these first (all free, no credit card required for the tiers we use):

| Service | URL | What you'll get |
|---|---|---|
| Neon | https://neon.tech | A Postgres connection string |
| Upstash | https://upstash.com | A Redis connection string |
| Fly.io | https://fly.io | Hosting for the API + worker |
| Vercel | https://vercel.com | Hosting for the Next.js site |
| Telegram | message [@BotFather](https://t.me/BotFather) | A bot token + username (alerts) |
| Google Cloud Console | https://console.cloud.google.com | An OAuth 2.0 Client ID (Google sign-in) |
| Brevo | https://www.brevo.com | An API key (OTP emails) |
| Razorpay | https://dashboard.razorpay.com | Test API keys (billing) |

## 1. Database — Neon

1. Create a project. Copy the connection string it gives you (it looks like
   `postgresql://user:pass@ep-xxx.neon.tech/dbname?sslmode=require`).
2. Rewrite it for our driver: replace `postgresql://` with
   `postgresql+psycopg://`. This is your `DATABASE_URL`.

## 2. Redis — Upstash

1. Create a Redis database (regional, not global — pick a region close to
   Fly's `bom` region or your Fly app's region).
2. Copy the "Redis URL" (`rediss://...`, note the double `s` — TLS). This is
   your `REDIS_URL`.

## 3. Telegram bot

1. Message [@BotFather](https://t.me/BotFather), run `/newbot`, follow the
   prompts. You get a token (`TELEGRAM_BOT_TOKEN`) and a username
   (`TELEGRAM_BOT_USERNAME`, without the `@`).
2. To get your own chat id for the daily admin report
   (`ADMIN_TELEGRAM_CHAT_ID`): message your new bot once, then open
   `https://api.telegram.org/bot<token>/getUpdates` in a browser and read
   `message.chat.id` from the JSON.
3. After deploying the API (step 6), register the webhook so `/start` deep
   links work:
   ```bash
   curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook?url=https://pricewalk-api.fly.dev/telegram/webhook"
   ```

## 4. Google sign-in

1. In Google Cloud Console, create an OAuth 2.0 Client ID (Web application).
2. Authorized JavaScript origins: your Vercel domain (e.g.
   `https://pricewalk.vercel.app`) and `http://localhost:3000` for local dev.
3. Copy the Client ID — it's both `GOOGLE_CLIENT_ID` (API) and
   `NEXT_PUBLIC_GOOGLE_CLIENT_ID` (web). The Client Secret isn't needed for
   this ID-token flow.

## 5. Brevo (OTP emails)

1. Create an account, go to SMTP & API > API Keys, generate one
   (`BREVO_API_KEY`).
2. Set `BREVO_SENDER_EMAIL` to any address — Brevo's free tier sends to any
   recipient without domain verification (see CLAUDE.md's stack notes).

## 6. API + worker — Fly.io

```bash
curl -L https://fly.io/install.sh | sh   # install flyctl
fly auth login
fly launch --no-deploy --copy-config --config infra/fly.toml
```

Set secrets (never commit these — this replaces `.env` in production):

```bash
fly secrets set \
  DATABASE_URL="postgresql+psycopg://..." \
  REDIS_URL="rediss://..." \
  CORS_ORIGINS="https://pricewalk.vercel.app" \
  JWT_SECRET="$(openssl rand -hex 32)" \
  GOOGLE_CLIENT_ID="..." \
  BREVO_API_KEY="..." \
  BREVO_SENDER_EMAIL="noreply@yourdomain.com" \
  TELEGRAM_BOT_TOKEN="..." \
  TELEGRAM_BOT_USERNAME="..." \
  ADMIN_TELEGRAM_CHAT_ID="..." \
  RAZORPAY_KEY_ID="..." \
  RAZORPAY_KEY_SECRET="..." \
  RAZORPAY_WEBHOOK_SECRET="..." \
  RAZORPAY_PLAN_ID_STARTER="..." \
  RAZORPAY_PLAN_ID_GROWTH="..." \
  AFFILIATE_TAG_AMAZON="..." \
  AFFILIATE_TAG_FLIPKART="..." \
  SENTRY_DSN="..."
```

Deploy (this also runs `alembic upgrade head` via `release_command` in
`infra/fly.toml`, before the new version takes traffic):

```bash
fly deploy --config infra/fly.toml
```

Scale the worker process to 1 machine (Fly's default `fly launch` only starts
the first process group it finds):

```bash
fly scale count api=1 worker=1
```

Verify: `curl https://pricewalk-api.fly.dev/health` should return
`{"status": "ok"}`.

## 7. Web — Vercel

1. Import the GitHub repo into Vercel.
2. Set **Root Directory** to `apps/web` in the project settings.
3. Add environment variables:
   - `NEXT_PUBLIC_API_URL` = `https://pricewalk-api.fly.dev`
   - `NEXT_PUBLIC_GOOGLE_CLIENT_ID` = (from step 4)
   - `JWT_SECRET` = **the exact same value** set on Fly (middleware.ts
     verifies the same cookie the API issues)
4. Deploy. Vercel builds and hosts the Next.js app with zero other config.
5. Make sure `CORS_ORIGINS` on Fly (step 6) matches this exact Vercel domain
   — it's read from the environment, no code change needed. Update it with
   `fly secrets set CORS_ORIGINS="https://your-domain.vercel.app"` if you set
   it before knowing the final domain.

## 8. Uptime check

Fly's own `http_checks` in `infra/fly.toml` restarts the API if `/health`
fails, but for an external alert when the whole app is down, add a free
[UptimeRobot](https://uptimerobot.com) monitor:

- Monitor type: HTTP(s)
- URL: `https://pricewalk-api.fly.dev/health`
- Interval: 5 minutes (free tier)

## 9. Razorpay webhook

In the Razorpay dashboard: Settings > Webhooks > Add New Webhook.

- URL: `https://pricewalk-api.fly.dev/webhooks/razorpay`
- Secret: generate one and set it as both the webhook secret in the
  dashboard and `RAZORPAY_WEBHOOK_SECRET` in Fly secrets.
- Active events: `subscription.activated`, `subscription.charged`,
  `subscription.pending`, `subscription.halted`, `subscription.cancelled`,
  `subscription.completed`.

Also create the two paid plans (Subscriptions > Plans) and put their ids in
`RAZORPAY_PLAN_ID_STARTER` / `RAZORPAY_PLAN_ID_GROWTH`.

## What's already wired for production

- **Structured JSON logs** (`core/logging_config.py`) on both api and
  worker — tokens/phone/email fields are redacted automatically.
- **Sentry** (`core/sentry.py`) — a no-op until `SENTRY_DSN` is set.
- **DB migrations on release** — `infra/fly.toml`'s `release_command` runs
  `alembic upgrade head` before every deploy.
- **Daily admin report** (worker cron, 8 AM IST) — products tracked, fetch
  success rate per domain, alerts sent, blocks detected, sent to
  `ADMIN_TELEGRAM_CHAT_ID`.

## Redeploying after code changes

```bash
fly deploy --config infra/fly.toml   # api + worker
# Vercel redeploys automatically on push to the connected branch.
```
