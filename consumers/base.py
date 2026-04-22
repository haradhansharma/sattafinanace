"""
Base WebSocket consumer for FinLife Personal Finance SaaS.

Provides authenticated, per-user WebSocket connections with:
  - JWT-based auth via query param
  - Channel group management (user-scoped + global broadcast)
  - JSON message protocol with typed events
  - Heartbeat / keep-alive
  - Reconnection resilience

All domain-specific consumers should inherit from BaseFinanceConsumer.
"""

import json
import logging
from typing import Optional

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------


@database_sync_to_async
def _resolve_user(user_id_str: str):
    """Look up a user by PK (called from async context)."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    try:
        return User.objects.get(pk=user_id_str)
    except User.DoesNotExist:
        return None


# ---------------------------------------------------------------------------
# Base Finance Consumer
# ---------------------------------------------------------------------------


class BaseFinanceConsumer(AsyncWebsocketConsumer):
    """
    Base authenticated WebSocket consumer.

    Auth: client sends ?token=<access_token> on connect.
    Groups:
      - "user_{user_id}" — personal notifications
      - Optional domain groups joined by subclass connect()

    Message protocol (JSON):
      {
        "type": "event_type",
        "data": { ... }
      }
    """

    # Subclasses override to set the domain (e.g., "bank", "expense")
    DOMAIN: str = "finance"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.user_id: Optional[str] = None
        self.user_group_name: Optional[str] = None

    # ==================== Lifecycle ====================

    async def connect(self):
        """Accept connection after JWT auth via query param."""
        token = self.scope["query_params"].get("token")
        if not token:
            await self.close(code=4001, reason="Missing token")
            return

        user_id_str = self._decode_user_id_from_token(token)
        if not user_id_str:
            await self.close(code=4003, reason="Invalid or expired token")
            return

        self.user = await _resolve_user(user_id_str)
        if not self.user or not self.user.is_active:
            await self.close(code=4003, reason="User not found or inactive")
            return

        self.user_id = str(self.user.id)
        self.user_group_name = f"user_{self.user_id}"

        # Join personal group
        await self.channel_layer.group_add(self.user_group_name, self.channel_name)

        # Let subclass join domain-specific groups
        await self.on_connected()

        await self.accept()
        logger.info("WebSocket connected: user=%s domain=%s", self.user_id, self.DOMAIN)

    async def disconnect(self, close_code):
        """Leave all groups on disconnect."""
        if self.user_group_name:
            await self.channel_layer.group_discard(
                self.user_group_name, self.channel_name
            )
        await self.on_disconnected(close_code)
        logger.info(
            "WebSocket disconnected: user=%s domain=%s code=%s",
            self.user_id,
            self.DOMAIN,
            close_code,
        )

    # ==================== Hooks for subclasses ====================

    async def on_connected(self):
        """Override to join domain groups after auth. Called inside connect()."""
        pass

    async def on_disconnected(self, close_code):
        """Override for cleanup. Called inside disconnect()."""
        pass

    # ==================== Receive ====================

    async def receive(self, text_data=None, bytes_data=None):
        """Parse JSON message and dispatch to handler."""
        if text_data is None:
            await self.send_json(
                {"type": "error", "data": {"message": "Empty message"}}
            )
            return

        try:
            message = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send_json({"type": "error", "data": {"message": "Invalid JSON"}})
            return

        msg_type = message.get("type", "")
        data = message.get("data", {})

        handler = getattr(self, f"handle_{msg_type}", None)
        if handler:
            try:
                await handler(data)
            except Exception as exc:
                logger.exception("WebSocket handler error: %s", msg_type)
                await self.send_json({"type": "error", "data": {"message": str(exc)}})
        else:
            await self.send_json(
                {"type": "error", "data": {"message": f"Unknown event: {msg_type}"}}
            )

    # ==================== Built-in handlers ====================

    async def handle_ping(self, data):
        """Heartbeat / keep-alive."""
        await self.send_json(
            {"type": "pong", "data": {"timestamp": data.get("timestamp")}}
        )

    async def handle_subscribe(self, data):
        """
        Subscribe to a domain-specific channel group.
        Client sends: {"type": "subscribe", "data": {"channel": "bank"}}
        """
        channel = data.get("channel", "")
        group_name = f"{channel}_{self.user_id}"
        await self.channel_layer.group_add(group_name, self.channel_name)
        await self.send_json({"type": "subscribed", "data": {"channel": channel}})

    async def handle_unsubscribe(self, data):
        """
        Unsubscribe from a domain-specific channel group.
        Client sends: {"type": "unsubscribe", "data": {"channel": "bank"}}
        """
        channel = data.get("channel", "")
        group_name = f"{channel}_{self.user_id}"
        await self.channel_layer.group_discard(group_name, self.channel_name)
        await self.send_json({"type": "unsubscribed", "data": {"channel": channel}})

    # ==================== Channel layer handlers ====================

    async def notification_event(self, event):
        """Generic notification pushed to user's personal group."""
        await self.send_json({"type": "notification", "data": event.get("data", {})})

    async def balance_update(self, event):
        """Real-time balance change pushed to subscribed group."""
        await self.send_json({"type": "balance_update", "data": event.get("data", {})})

    async def transaction_alert(self, event):
        """New transaction notification pushed to subscribed group."""
        await self.send_json(
            {"type": "transaction_alert", "data": event.get("data", {})}
        )

    async def reminder_alert(self, event):
        """Bill/EMI/insurance reminder pushed to subscribed group."""
        await self.send_json({"type": "reminder_alert", "data": event.get("data", {})})

    # ==================== Helpers ====================

    def _decode_user_id_from_token(self, token: str) -> Optional[str]:
        """Decode user_id from a ninja_jwt access token (sync, no DB hit)."""
        try:
            from ninja_jwt.tokens import AccessToken
            from django.conf import settings

            access_token = AccessToken(token)
            # Try common claim keys
            user_id = (
                access_token.get(settings.AUTH_USER_MODEL + " id")
                or access_token.get("user_id")
                or None
            )
            return str(user_id) if user_id else None
        except Exception:
            return None

    @staticmethod
    async def send_to_user(user_id: str, event_type: str, data: dict):
        """
        Class-level helper to push an event to a specific user's WebSocket.

        Usage (from Celery task or view):
            await BaseFinanceConsumer.send_to_user(
                user_id="uuid-here",
                event_type="notification",
                data={"title": "Payment Due", "message": "Your EMI is due tomorrow"}
            )
        """
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f"user_{user_id}",
            {"type": event_type, "data": data},
        )

    @staticmethod
    async def send_to_group(group_name: str, event_type: str, data: dict):
        """
        Class-level helper to push an event to a channel group.

        Usage:
            await BaseFinanceConsumer.send_to_group(
                group_name="bank_uuid-here",
                event_type="balance_update",
                data={"account_id": "...", "new_balance": 50000}
            )
        """
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            group_name,
            {"type": event_type, "data": data},
        )
