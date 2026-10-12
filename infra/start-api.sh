#!/bin/sh
set -e
alembic -c packages/core/alembic.ini upgrade head
exec uvicorn api.main:app --host 0.0.0.0 --port "$PORT"
