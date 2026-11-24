"""Pre-P7 development identity; this is not authentication."""

from dataclasses import dataclass

from apps.api.config import Settings


class AuthenticationRequiredError(PermissionError):
    """Raised when development identity is requested outside a dev context."""


@dataclass(frozen=True)
class DevelopmentIdentity:
    user_id: str
    is_authenticated: bool = False
    scheme: str = "development-only"


def get_development_identity(settings: Settings) -> DevelopmentIdentity:
    if settings.environment not in {"development", "test"}:
        raise AuthenticationRequiredError("Development identity is unavailable in production")
    return DevelopmentIdentity(user_id=settings.development_user_id)
