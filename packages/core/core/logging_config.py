import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

# Fields CLAUDE.md forbids logging at INFO: tokens, phone numbers, emails.
_REDACTED_KEYS = {"token", "phone", "email", "password", "authorization"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        for key, value in record.__dict__.items():
            if key in _REDACTED_KEYS:
                payload[key] = "[redacted]"
            elif key not in logging.LogRecord("", 0, "", 0, "", (), None).__dict__ and key not in (
                "message",
            ):
                payload[key] = value

        return json.dumps(payload, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
