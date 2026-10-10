from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import admin, auth, billing, buyer, health, redirect, seller, telegram
from core.logging_config import configure_logging
from core.sentry import init_sentry
from core.settings import get_settings

configure_logging()
init_sentry()

app = FastAPI(title="PriceWalk API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(telegram.router)
app.include_router(seller.router)
app.include_router(buyer.router)
app.include_router(redirect.router)
app.include_router(billing.router)
