import json
import logging

from core.logging_config import JsonFormatter


def _make_record(msg: str, **extra: object) -> logging.LogRecord:
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname="x.py",
        lineno=1,
        msg=msg,
        args=(),
        exc_info=None,
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_formats_as_json_with_core_fields() -> None:
    record = _make_record("hello world")
    output = json.loads(JsonFormatter().format(record))

    assert output["message"] == "hello world"
    assert output["level"] == "INFO"
    assert output["logger"] == "test.logger"
    assert "ts" in output


def test_redacts_sensitive_extra_fields() -> None:
    record = _make_record("user logged in", email="user@example.com", phone="+919999999999")
    output = json.loads(JsonFormatter().format(record))

    assert output["email"] == "[redacted]"
    assert output["phone"] == "[redacted]"


def test_preserves_non_sensitive_extra_fields() -> None:
    record = _make_record("fetch ok", domain="www.amazon.in", status_code=200)
    output = json.loads(JsonFormatter().format(record))

    assert output["domain"] == "www.amazon.in"
    assert output["status_code"] == 200
