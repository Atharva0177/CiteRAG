"""Validated configuration with environment-only provider secrets."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

import yaml


class ConfigurationError(ValueError):
    """Raised when configuration is missing, malformed, or unsafe."""


@dataclass(frozen=True)
class Settings:
    environment: str
    fixtures_only: bool
    development_user_id: str
    log_level: str
    nim_api_key: str | None = field(default=None, repr=False)
    allow_live_nim: bool = False
    live_call_reason: str = ""


def _parse_bool(name: str, value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off", ""}:
        return False
    raise ConfigurationError(f"{name} must be a boolean, got {value!r}")


def load_settings(
    path: str | Path = Path("config/settings.yaml"),
    *,
    environ: Mapping[str, str] | None = None,
) -> Settings:
    """Load non-secret YAML settings and explicit live-call controls."""

    config_path = Path(path)
    env = os.environ if environ is None else environ
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigurationError(f"Cannot load configuration {config_path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigurationError("Configuration root must be a mapping")

    defaults = {
        "environment": "development",
        "fixtures_only": True,
        "development_user_id": "dev-local",
        "log_level": "INFO",
    }
    unknown = set(raw) - set(defaults)
    if unknown:
        names = ", ".join(sorted(str(key) for key in unknown))
        raise ConfigurationError(f"Unknown configuration keys: {names}")
    values = defaults | raw

    if not isinstance(values["environment"], str) or values["environment"] not in {"development", "test", "production"}:
        raise ConfigurationError("environment must be development, test, or production")
    if not isinstance(values["fixtures_only"], bool):
        raise ConfigurationError("fixtures_only must be a boolean")
    if not isinstance(values["development_user_id"], str) or not values["development_user_id"].strip():
        raise ConfigurationError("development_user_id must be a non-empty string")
    if not isinstance(values["log_level"], str) or values["log_level"] not in {
        "CRITICAL",
        "ERROR",
        "WARNING",
        "INFO",
        "DEBUG",
    }:
        raise ConfigurationError("log_level must be a standard logging level")

    return Settings(
        environment=values["environment"],
        fixtures_only=values["fixtures_only"],
        development_user_id=values["development_user_id"].strip(),
        log_level=values["log_level"],
        nim_api_key=env.get("NVIDIA_API_KEY") or None,
        allow_live_nim=_parse_bool("CITERAG_ALLOW_LIVE_NIM", env.get("CITERAG_ALLOW_LIVE_NIM", "false")),
        live_call_reason=env.get("CITERAG_LIVE_CALL_REASON", "").strip(),
    )
