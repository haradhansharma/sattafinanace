"""
JWT authentication helpers for FinLife.
Uses ninja_jwt for token creation/verification.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

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


def get_current_user_from_token(token: str):
    """
    Validate a JWT token and return the User instance.
    Returns None if token is invalid or expired.
    """
    try:
        # ninja_jwt AccessToken validates automatically
        access_token = AccessToken(token)
        user_id = (
            access_token.get(settings.AUTH_USER_MODEL + " id")
            or access_token.get(api_settings.USER_ID_FIELD)
            or access_token.get("user_id")
        )
        if user_id is None:
            return None
        return User.objects.get(pk=user_id)
    except Exception:
        return None
