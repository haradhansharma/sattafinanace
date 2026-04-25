from datetime import datetime
from typing import Optional
from ninja import Schema
from pydantic import Field


class NotificationPreferenceSchema(Schema):
    """Matches frontend NotificationPreference interface exactly."""

    email: bool = True
    push: bool = True
    budgetAlert: bool = True
    lowBalance: bool = True
    loanReminder: bool = True


class UserOut(Schema):
    """
    Full user response matching frontend User type.
    Fields: id, slug, name, email, avatar, currency, dateFormat,
            darkMode, notifications, createdAt, updatedAt
    """

    id: str
    slug: str = ""
    name: str
    email: str
    avatar: str = ""
    currency: str
    dateFormat: str
    darkMode: bool
    notifications: NotificationPreferenceSchema
    createdAt: str
    updatedAt: str

    @staticmethod
    def resolve_id(obj):
        return str(obj.id)

    @staticmethod
    def resolve_slug(obj):
        return str(obj.slug) if obj.slug else ""

    @staticmethod
    def resolve_avatar(obj):
        return obj.avatar or ""

    @staticmethod
    def resolve_dateFormat(obj):
        return obj.date_format

    @staticmethod
    def resolve_darkMode(obj):
        return obj.dark_mode

    @staticmethod
    def resolve_notifications(obj):
        # notifications is a JSONField (dict) — wrap in schema
        notif = obj.notifications
        if isinstance(notif, dict):
            return NotificationPreferenceSchema(**notif)
        return NotificationPreferenceSchema()

    @staticmethod
    def resolve_createdAt(obj):
        return obj.created_at.isoformat()

    @staticmethod
    def resolve_updatedAt(obj):
        return obj.updated_at.isoformat()


class UserCreate(Schema):
    """Registration schema — matches frontend login(name, email, password)."""

    name: str
    email: str
    password: str
    currency: str = "BDT"
    dateFormat: str = "dd/MM/yyyy"
    darkMode: bool = False


class UserLogin(Schema):
    """Login schema — matches frontend login(email, password)."""

    email: str
    password: str


class UserUpdate(Schema):
    """Profile update schema — all fields optional for PATCH-like behavior."""

    name: Optional[str] = None
    avatar: Optional[str] = None
    currency: Optional[str] = None
    dateFormat: Optional[str] = None
    darkMode: Optional[bool] = None
    notifications: Optional[NotificationPreferenceSchema] = None


class TokenOut(Schema):
    """Token response after login/register — matches frontend auth store state."""

    access: str
    refresh: Optional[str] = Field(
        default=None, description="Refresh token for token rotation"
    )
    token_type: str = "bearer"
    user: UserOut


class MessageOut(Schema):
    """Generic message response."""

    message: str


# ==================== OTP Schemas ====================


class OTPVerifyIn(Schema):
    """OTP verification — works for registration, login, and password change."""

    email: str
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")
    purpose: str = Field(
        ...,
        pattern="^(register|login|change_password|forgot_password)$",
        description="'register', 'login', 'change_password', or 'forgot_password'",
    )


class ResendOtpIn(Schema):
    """Request a new OTP to be sent."""

    email: str
    purpose: str = Field(
        ...,
        pattern="^(register|login|change_password|forgot_password)$",
        description="'register', 'login', 'change_password', or 'forgot_password'",
    )


class ChangePasswordIn(Schema):
    """Password change request — requires current password."""

    current_password: str = Field(..., min_length=4, description="Current password")


class ForgotPasswordIn(Schema):
    """Forgot password request — requires email only."""

    email: str = Field(..., description="Registered email address")


class ForgotPasswordConfirmIn(Schema):
    """Forgot password confirmation — requires OTP and new password."""

    email: str
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")
    new_password: str = Field(
        ..., min_length=4, description="New password (min 4 chars)"
    )


class ChangePasswordConfirmIn(Schema):
    """Password change confirmation — requires OTP and new password."""

    email: str
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")
    new_password: str = Field(
        ..., min_length=4, description="New password (min 4 chars)"
    )


class ForgotPasswordIn(Schema):
    """Forgot password request — requires email only."""

    email: str = Field(..., description="Registered email address")


class ForgotPasswordConfirmIn(Schema):
    """Forgot password confirmation — requires OTP and new password."""

    email: str
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")
    new_password: str = Field(
        ..., min_length=4, description="New password (min 4 chars)"
    )


# ==================== Token Schemas ====================


class RefreshTokenIn(Schema):
    """Refresh token request."""

    refresh: str = Field(..., description="Refresh token")


class RefreshTokenOut(Schema):
    """Refresh token response."""

    access: str
    refresh: str = None
    token_type: str = "bearer"
