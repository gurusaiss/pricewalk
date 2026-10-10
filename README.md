# PriceWalk

Price tracking for Indian e-commerce. See [CLAUDE.md](CLAUDE.md) for product spec and conventions,
[PROMPTS.md](PROMPTS.md) for the milestone plan.

## Stack (all free tiers / self-hosted)

- API: FastAPI (Python 3.12) + SQLAlchemy 2.0 + Alembic
- Jobs: Redis + `arq`
- DB: PostgreSQL 16
- Web: Next.js 14 + TypeScript + Tailwind + shadcn/ui
- Local dev: Docker Compose

## Run it

1. Copy the env file and adjust if needed (defaults match docker-compose):

   ```bash
   cp .env.example .env
   ```

2. Start everything:

   ```bash
   make dev
   ```

   (or directly: `docker compose -f infra/docker-compose.yml up --build`)

   - API: http://localhost:8000/health
   - Web: http://localhost:3000
   - Postgres: localhost:5432 (user/pass/db: `pricewalk`)
   - Redis: localhost:6379

3. Stop everything: `make down`

## Local development without Docker

Python (API + worker + core):

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash; use .venv/bin/activate on macOS/Linux
pip install -e ".[dev]"
uvicorn api.main:app --reload            # run the API
arq worker.main.WorkerSettings           # run the worker
pytest                                   # run tests
```

Web:

```bash
cd apps/web
npm install
npm run dev
```

## Common tasks

```bash
make test       # pytest + next build
make lint       # ruff + mypy + eslint
make format     # ruff format + prettier
make migrate    # alembic upgrade head (packages/core)
make migration m="add users table"   # new alembic revision
```

## Checking a real product page manually

```bash
python -m core.fetch "https://www.amazon.in/dp/B08N5WRWNW"
```

Prints the parsed marketplace, id, and `ProductSnapshot` (title/price/stock/etc.) as
JSON. Needs Redis running (`REDIS_URL`) for the per-domain rate limiter and
block/CAPTCHA pause tracking. If the plain HTML fetch doesn't find a price, it
falls back to a headless-browser render via Playwright - run `playwright install
chromium` once before relying on that path.

## Database migrations

Alembic lives in `packages/core`. With a database reachable at `DATABASE_URL`:

```bash
cd packages/core
alembic revision --autogenerate -m "message"
alembic upgrade head
```
