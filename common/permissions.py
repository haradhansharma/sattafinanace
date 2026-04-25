"""
Django Ninja authentication classes for FinLife.
Uses BearerAuth (JWT) for all authenticated endpoints.
Supports both sync and async views.
"""

from django.contrib.auth import get_user_model
from ninja.security import HttpBearer

from .auth import get_current_user_id_from_token

User = get_user_model()


class BearerAuth(HttpBearer):
    """
    JWT Bearer token authentication.
    Sets request.user to the authenticated User instance.
    Returns the token string on success, None on failure.

    Supports async views — Django Ninja detects coroutine functions
    and awaits them automatically.
    """

    async def authenticate(self, request, token):
        user_id = get_current_user_id_from_token(token)
        if user_id is None:
            return None

        try:
            user = await User.objects.aget(pk=user_id)
            if user and user.is_active:
                request.user = user
                return token
        except User.DoesNotExist:
            pass

        return None
