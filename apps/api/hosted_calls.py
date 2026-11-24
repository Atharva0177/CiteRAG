"""Explicit authorization boundary for hosted model procedures."""

from apps.api.config import Settings


class HostedCallError(PermissionError):
    """Raised when a hosted call violates fixture/live procedure policy."""


def assert_hosted_call_allowed(settings: Settings) -> None:
    """Require fixture mode to be disabled and live use to be explicit."""

    if settings.fixtures_only:
        raise HostedCallError("Configuration is fixtures only; hosted calls are disabled")
    if not settings.allow_live_nim:
        raise HostedCallError("Set CITERAG_ALLOW_LIVE_NIM=true for an authorized live procedure")
    if not settings.nim_api_key:
        raise HostedCallError("NVIDIA_API_KEY is required for an authorized live procedure")
    if not settings.live_call_reason:
        raise HostedCallError("CITERAG_LIVE_CALL_REASON must identify the live procedure")
