"""Structured JSON logging with defense-in-depth secret redaction."""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any, TextIO

from apps.api.config import Settings

REDACTED = "[REDACTED]"
_BEARER = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")
_SENSITIVE_KEYS = {
    "apikey",
    "authorization",
    "proxyauthorization",
    "cookie",
    "setcookie",
    "password",
    "passwd",
    "secret",
    "token",
    "accesstoken",
    "refreshtoken",
    "credential",
    "credentials",
}
_RESERVED_RECORD_KEYS = set(logging.makeLogRecord({}).__dict__) | {"message", "asctime"}


def _normalized_key(key: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(key).lower())


def _redact_text(value: str, secrets: tuple[str, ...]) -> str:
    redacted = value
    for secret in sorted((item for item in secrets if item), key=len, reverse=True):
        redacted = redacted.replace(secret, REDACTED)
    return _BEARER.sub(f"Bearer {REDACTED}", redacted)


def redact(value: Any, *, secrets: tuple[str, ...] = ()) -> Any:
    """Recursively redact sensitive keys, known secrets, and bearer tokens."""

    if isinstance(value, dict):
        return {
            key: REDACTED if _normalized_key(key) in _SENSITIVE_KEYS else redact(item, secrets=secrets)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact(item, secrets=secrets) for item in value]
    if isinstance(value, str):
        return _redact_text(value, secrets)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return _redact_text(str(value), secrets)


class JsonLogFormatter(logging.Formatter):
    def __init__(self, *, secrets: tuple[str, ...] = ()) -> None:
        super().__init__()
        self._secrets = secrets

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds")
        payload = {
            "timestamp": timestamp.replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": _redact_text(record.getMessage(), self._secrets),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED_RECORD_KEYS:
                payload[key] = redact(value, secrets=self._secrets)
        if record.exc_info:
            payload["exception"] = _redact_text(self.formatException(record.exc_info), self._secrets)
        if record.stack_info:
            payload["stack"] = _redact_text(self.formatStack(record.stack_info), self._secrets)
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def configure_logging(settings: Settings, *, stream: TextIO | None = None) -> logging.Logger:
    """Configure the application logger without leaking provider credentials."""

    logger = logging.getLogger("citerag")
    logger.setLevel(settings.log_level)
    logger.propagate = False
    for handler in logger.handlers:
        logger.removeHandler(handler)
        handler.close()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonLogFormatter(secrets=(settings.nim_api_key,) if settings.nim_api_key else ()))
    logger.addHandler(handler)
    return logger
