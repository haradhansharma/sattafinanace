"""
WebSocket URL routing for FinLife.

All WebSocket connections go through /ws/{domain}/ where domain
matches a registered consumer (e.g., bank, expense, notification).
"""

from django.urls import re_path

from .notification import NotificationConsumer

websocket_urlpatterns = [
    re_path(r"ws/notification/$", NotificationConsumer.as_asgi()),
]
