#!/bin/sh
set -e
# alembic.ini's script_location is relative to the current working
# directory, not the ini file's location, so this must run from
# packages/core (see Makefile's `migrate` target for the same pattern).
(cd packages/core && alembic upgrade head)
exec uvicorn api.main:app --host 0.0.0.0 --port "$PORT"
