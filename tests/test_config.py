from pathlib import Path

import pytest

from apps.api.config import ConfigurationError, load_settings


def write_config(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "settings.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_load_settings_uses_safe_fixture_defaults(tmp_path):
    path = write_config(
        tmp_path,
        "environment: development\nfixtures_only: true\ndevelopment_user_id: dev-local\nlog_level: INFO\n",
    )

    settings = load_settings(path, environ={})

    assert settings.environment == "development"
    assert settings.fixtures_only is True
    assert settings.development_user_id == "dev-local"
    assert settings.allow_live_nim is False
    assert settings.nim_api_key is None


def test_environment_values_control_explicit_live_procedure(tmp_path):
    path = write_config(
        tmp_path,
        "environment: test\nfixtures_only: false\ndevelopment_user_id: test-user\nlog_level: DEBUG\n",
    )

    settings = load_settings(
        path,
        environ={
            "NVIDIA_API_KEY": "nvapi-test-secret",
            "CITERAG_ALLOW_LIVE_NIM": "true",
            "CITERAG_LIVE_CALL_REASON": "P0 smoke test",
        },
    )

    assert settings.nim_api_key == "nvapi-test-secret"
    assert settings.allow_live_nim is True
    assert settings.live_call_reason == "P0 smoke test"
    assert "nvapi-test-secret" not in repr(settings)


def test_unknown_config_keys_are_rejected(tmp_path):
    path = write_config(tmp_path, "environment: test\nunknown_option: value\n")

    with pytest.raises(ConfigurationError, match="unknown_option"):
        load_settings(path, environ={})


@pytest.mark.parametrize(
    "config_text",
    [
        "123: unexpected\n",
        "environment: []\n",
        "log_level: []\n",
    ],
)
def test_non_scalar_and_non_string_config_values_fail_cleanly(tmp_path, config_text):
    path = write_config(tmp_path, config_text)

    with pytest.raises(ConfigurationError):
        load_settings(path, environ={})


def test_invalid_live_flag_is_rejected(tmp_path):
    path = write_config(tmp_path, "environment: test\n")

    with pytest.raises(ConfigurationError, match="CITERAG_ALLOW_LIVE_NIM"):
        load_settings(path, environ={"CITERAG_ALLOW_LIVE_NIM": "sometimes"})


def test_empty_development_identity_is_rejected(tmp_path):
    path = write_config(tmp_path, "development_user_id: '  '\n")

    with pytest.raises(ConfigurationError, match="development_user_id"):
        load_settings(path, environ={})
