import json
import socket

import pytest

from apps.api.config import load_settings
from apps.api.hosted_calls import HostedCallError, assert_hosted_call_allowed
from apps.api.identity import AuthenticationRequiredError, get_development_identity
from apps.api.observability import configure_logging


def make_settings(tmp_path, config_text="environment: test\n", **environ):
    path = tmp_path / "settings.yaml"
    path.write_text(config_text, encoding="utf-8")
    return load_settings(path, environ=environ)


def test_fixture_policy_denies_live_call_even_when_key_exists(tmp_path):
    settings = make_settings(tmp_path, NVIDIA_API_KEY="nvapi-test-secret")

    with pytest.raises(HostedCallError, match="fixtures only"):
        assert_hosted_call_allowed(settings)


def test_live_procedure_requires_explicit_flag_key_and_reason(tmp_path):
    config = "environment: test\nfixtures_only: false\n"
    cases = [
        {},
        {"CITERAG_ALLOW_LIVE_NIM": "true"},
        {
            "CITERAG_ALLOW_LIVE_NIM": "true",
            "NVIDIA_API_KEY": "nvapi-test-secret",
        },
    ]

    for environ in cases:
        settings = make_settings(tmp_path, config, **environ)
        with pytest.raises(HostedCallError):
            assert_hosted_call_allowed(settings)

    allowed = make_settings(
        tmp_path,
        config,
        CITERAG_ALLOW_LIVE_NIM="true",
        NVIDIA_API_KEY="nvapi-test-secret",
        CITERAG_LIVE_CALL_REASON="P0 authorized smoke test",
    )
    assert_hosted_call_allowed(allowed)


def test_development_identity_never_claims_real_authentication(tmp_path):
    settings = make_settings(tmp_path, "environment: development\ndevelopment_user_id: dev-local\n")

    identity = get_development_identity(settings)

    assert identity.user_id == "dev-local"
    assert identity.is_authenticated is False
    assert identity.scheme == "development-only"


def test_development_identity_is_unavailable_in_production(tmp_path):
    settings = make_settings(tmp_path, "environment: production\n")

    with pytest.raises(AuthenticationRequiredError):
        get_development_identity(settings)


def test_structured_logs_redact_configured_and_bearer_secrets(tmp_path):
    secret = "nvapi-test-secret"
    settings = make_settings(tmp_path, NVIDIA_API_KEY=secret)
    from io import StringIO

    stream = StringIO()
    logger = configure_logging(settings, stream=stream)
    logger.info(
        "key=%s bearer=Bearer another-secret",
        secret,
        extra={
            "trace_id": "trace-123",
            "context": {"Authorization": f"Bearer {secret}", "safe": "visible"},
        },
    )

    raw = stream.getvalue()
    event = json.loads(raw)
    assert secret not in raw
    assert "another-secret" not in raw
    assert event["trace_id"] == "trace-123"
    assert event["context"] == {"Authorization": "[REDACTED]", "safe": "visible"}
    assert event["level"] == "INFO"


def test_network_guard_blocks_real_socket_connections():
    with pytest.raises(RuntimeError, match="Network access is disabled"):
        socket.create_connection(("127.0.0.1", 9), timeout=0.01)
