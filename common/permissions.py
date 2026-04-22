"""
Django Ninja authentication classes for FinLife.
Uses BearerAuth (JWT) for all authenticated endpoints.
"""

from ninja.security import HttpBearer

from .auth import get_current_user_from_token


class BearerAuth(HttpBearer):
    """
    JWT Bearer token authentication.
    Sets request.user to the authenticated User instance.
    Returns the token string on success, None on failure.
    """

    def authenticate(self, request, token):
        user = get_current_user_from_token(token)
        if user and user.is_active:
            request.user = user
            return token
        return None
