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
    Fields: id, name, email, avatar, currency, dateFormat,
            darkMode, notifications, createdAt, updatedAt
    """

    id: str
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
    refresh: Optional[str] = Field(default=None, description="Refresh token for token rotation")
    token_type: str = "bearer"
    user: UserOut


class MessageOut(Schema):
    """Generic message response."""

    message: str
