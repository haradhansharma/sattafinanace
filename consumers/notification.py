"""
Notification WebSocket consumer.

Connected clients receive real-time push notifications for:
  - Bill payment reminders
  - Savings goal milestones
  - Loan EMI due alerts
  - Investment maturity alerts
  - Low balance warnings
  - Transaction confirmations

Connect: ws://host/ws/notification/?token=<access_token>
"""

import logging

from channels.db import database_sync_to_async
from channels.layers import get_channel_layer

from .base import BaseFinanceConsumer

logger = logging.getLogger(__name__)


class NotificationConsumer(BaseFinanceConsumer):
    """
    Dedicated notification WebSocket.

    Protocol:
      Server → Client:
        {"type": "notification", "data": {"id": "...", "title": "...", "body": "...", "category": "...", "read": false}}

      Client → Server:
        {"type": "ping", "data": {"timestamp": "..."}}
        {"type": "mark_read", "data": {"notification_id": "..."}}

    Events received from channel layer:
      - notification_event  → generic notification
      - reminder_alert      → bill/EMI/insurance reminder
      - balance_update      → account balance change
      - transaction_alert   → new transaction
    """

    DOMAIN = "notification"

    async def on_connected(self):
        """Join the global notification group for this user."""
        group = f"notifications_{self.user_id}"
        await self.channel_layer.group_add(group, self.channel_name)

    async def handle_mark_read(self, data):
        """Mark a notification as read (persisted via DB call)."""
        notification_id = data.get("notification_id")
        if not notification_id:
            await self.send_json(
                {"type": "error", "data": {"message": "notification_id required"}}
            )
            return

        success = await self._mark_notification_read(notification_id)
        if success:
            await self.send_json(
                {
                    "type": "notification_read",
                    "data": {"notification_id": notification_id},
                }
            )
        else:
            await self.send_json(
                {
                    "type": "error",
                    "data": {"message": "Notification not found"},
                }
            )

    async def handle_subscribe_alerts(self, data):
        """Subscribe to specific alert types: bill, loan, insurance, investment, savings."""
        alert_type = data.get("alert_type", "")
        if alert_type:
            group = f"alert_{alert_type}_{self.user_id}"
            await self.channel_layer.group_add(group, self.channel_name)
            await self.send_json(
                {
                    "type": "alerts_subscribed",
                    "data": {"alert_type": alert_type},
                }
            )

    async def handle_unsubscribe_alerts(self, data):
        """Unsubscribe from specific alert types."""
        alert_type = data.get("alert_type", "")
        if alert_type:
            group = f"alert_{alert_type}_{self.user_id}"
            await self.channel_layer.group_discard(group, self.channel_name)
            await self.send_json(
                {
                    "type": "alerts_unsubscribed",
                    "data": {"alert_type": alert_type},
                }
            )

    # ==================== Channel layer event handlers ====================

    async def bill_reminder(self, event):
        """Bill payment due reminder."""
        await self.send_json({"type": "bill_reminder", "data": event.get("data", {})})

    async def loan_emi_due(self, event):
        """Loan EMI payment reminder."""
        await self.send_json({"type": "loan_emi_due", "data": event.get("data", {})})

    async def insurance_premium_due(self, event):
        """Insurance premium reminder."""
        await self.send_json(
            {"type": "insurance_premium_due", "data": event.get("data", {})}
        )

    async def savings_milestone(self, event):
        """Savings goal milestone achieved."""
        await self.send_json(
            {"type": "savings_milestone", "data": event.get("data", {})}
        )

    async def investment_maturity(self, event):
        """Investment maturity alert."""
        await self.send_json(
            {"type": "investment_maturity", "data": event.get("data", {})}
        )

    async def low_balance(self, event):
        """Low account balance warning."""
        await self.send_json({"type": "low_balance", "data": event.get("data", {})})

    async def transaction_created(self, event):
        """New transaction notification."""
        await self.send_json(
            {"type": "transaction_created", "data": event.get("data", {})}
        )

    # ==================== DB helpers ====================

    @database_sync_to_async
    def _mark_notification_read(self, notification_id: str) -> bool:
        """
        Mark a notification as read in the database.
        Returns True if found and updated, False otherwise.

        NOTE: When the Notification model is created, update this method
        to query the actual model. For now it's a placeholder.
        """
        # TODO: Update when Notification model exists
        # from apps.notification.models import Notification
        # try:
        #     notif = Notification.objects.get(id=notification_id, owner_id=self.user_id)
        #     notif.is_read = True
        #     notif.save(update_fields=["is_read", "updated_at"])
        #     return True
        # except Notification.DoesNotExist:
        #     return False
        return True
