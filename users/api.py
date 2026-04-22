from django.contrib.auth import get_user_model
from django.db import IntegrityError
from ninja import Router, Schema
from pydantic import Field

from common.permissions import BearerAuth
from .schemas import (
    MessageOut,
    NotificationPreferenceSchema,
    TokenOut,
    UserCreate,
    UserLogin,
    UserOut,
    UserUpdate,
)

User = get_user_model()
router = Router(tags=["Auth"])


# ==================== Registration ====================


@router.post("/register/", response={201: TokenOut, 400: MessageOut})
async def register(request, payload: UserCreate):
    """Register a new user and return JWT tokens."""
    if User.objects.filter(email=payload.email).exists():
        return 400, {"message": "Email already registered."}

    try:
        user = User.objects.create_user(
            email=payload.email,
            password=payload.password,
            name=payload.name,
            currency=payload.currency,
            date_format=payload.dateFormat,
            dark_mode=payload.darkMode,
        )
    except (ValueError, IntegrityError) as e:
        return 400, {"message": str(e)}

    from common.auth import create_token_pair

    tokens = create_token_pair(user)
    return 201, {
        "access": tokens["access"],
        "refresh": tokens["refresh"],
        "token_type": "bearer",
        "user": user,
    }


# ==================== Login ====================


@router.post("/login/", response={200: TokenOut, 401: MessageOut})
async def login(request, payload: UserLogin):
    """Authenticate user and return JWT tokens."""
    try:
        user = User.objects.get(email=payload.email)
    except User.DoesNotExist:
        return 401, {"message": "Invalid email or password."}

    if not user.check_password(payload.password):
        return 401, {"message": "Invalid email or password."}

    if not user.is_active:
        return 401, {"message": "Account is deactivated."}

    from common.auth import create_token_pair

    tokens = create_token_pair(user)
    return {
        "access": tokens["access"],
        "refresh": tokens["refresh"],
        "token_type": "bearer",
        "user": user,
    }


# ==================== Refresh Token ====================


class RefreshTokenIn(Schema):
    refresh: str = Field(..., description="Refresh token")


class RefreshTokenOut(Schema):
    access: str
    refresh: str = None
    token_type: str = "bearer"


@router.post("/refresh/", response={200: RefreshTokenOut, 401: MessageOut})
async def refresh_token(request, payload: RefreshTokenIn):
    """Exchange a refresh token for new access (and optionally refresh) token."""
    from ninja_jwt.tokens import RefreshToken

    try:
        refresh = RefreshToken(payload.refresh)
        user_id = refresh.get("user_id")
        if not user_id:
            return 401, {"message": "Invalid refresh token."}

        user = User.objects.get(pk=user_id)
        if not user.is_active:
            return 401, {"message": "User account is deactivated."}

        from common.auth import create_token_pair

        tokens = create_token_pair(user)
        return {
            "access": tokens["access"],
            "refresh": tokens["refresh"],
            "token_type": "bearer",
        }
    except Exception:
        return 401, {"message": "Invalid or expired refresh token."}


# ==================== Logout ====================


@router.post("/logout/", auth=BearerAuth(), response={200: MessageOut})
async def logout(request):
    """Logout endpoint (stateless — client discards token)."""
    return {"message": "Successfully logged out."}


# ==================== Get Current User ====================


@router.get("/me/", auth=BearerAuth(), response=UserOut)
async def get_me(request):
    """Get current authenticated user profile."""
    return request.user


# ==================== Update Current User ====================


@router.put("/me/", auth=BearerAuth(), response=UserOut)
async def update_me(request, payload: UserUpdate):
    """Update current authenticated user profile."""
    user = request.user

    update_fields = []
    if payload.name is not None:
        user.name = payload.name
        update_fields.append("name")
    if payload.avatar is not None:
        user.avatar = payload.avatar
        update_fields.append("avatar")
    if payload.currency is not None:
        user.currency = payload.currency
        update_fields.append("currency")
    if payload.dateFormat is not None:
        user.date_format = payload.dateFormat
        update_fields.append("date_format")
    if payload.darkMode is not None:
        user.dark_mode = payload.darkMode
        update_fields.append("dark_mode")
    if payload.notifications is not None:
        user.notifications = payload.notifications.model_dump()
        update_fields.append("notifications")

    if update_fields:
        user.save(update_fields=update_fields)
        user.refresh_from_db()
    return user


# ==================== Notification Preferences ====================


@router.get(
    "/me/preferences/", auth=BearerAuth(), response=NotificationPreferenceSchema
)
async def get_preferences(request):
    """Get current user notification preferences."""
    notif = request.user.notifications
    if isinstance(notif, dict):
        return NotificationPreferenceSchema(**notif)
    return NotificationPreferenceSchema()


@router.put(
    "/me/preferences/", auth=BearerAuth(), response=NotificationPreferenceSchema
)
async def update_preferences(request, payload: NotificationPreferenceSchema):
    """Update current user notification preferences."""
    user = request.user
    user.notifications = payload.model_dump()
    user.save(update_fields=["notifications", "updated_at"])
    user.refresh_from_db()
    notif = user.notifications
    if isinstance(notif, dict):
        return NotificationPreferenceSchema(**notif)
    return NotificationPreferenceSchema()
