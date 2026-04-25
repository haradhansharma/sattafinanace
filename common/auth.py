"""
JWT authentication helpers for FinLife.
Uses ninja_jwt for token creation/verification.

Note: get_current_user_id_from_token() is a SYNC, CPU-only function
(no DB calls) — safe to call from async context.
"""

from django.conf import settings
from django.contrib.auth import get_user_model

from ninja_jwt.settings import api_settings
from ninja_jwt.tokens import RefreshToken, AccessToken

User = get_user_model()


def create_token(user) -> str:
    """
    Create JWT access token for the given user.
    Uses ninja_jwt's built-in token backend.
    """
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


def create_token_pair(user) -> dict:
    """
    Create both access and refresh tokens.
    Returns: {"access": str, "refresh": str}
    """
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def get_current_user_id_from_token(token: str):
    """
    Validate a JWT token and return the user ID (UUID string).
    Returns None if token is invalid or expired.

    This function is SYNC and CPU-only (no DB calls).
    Callers should do the async User.objects.aget() themselves.
    """
    try:
        access_token = AccessToken(token)
        user_id = (
            access_token.get(settings.AUTH_USER_MODEL + " id")
            or access_token.get(api_settings.USER_ID_FIELD)
            or access_token.get("user_id")
        )
        return user_id
    except Exception:
        return None
