# backend/config/asgi.py

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(
                [
                    # WebSocket routes
                    # ws://host/ws/notification/?token=<access_token>
                    # ws://host/ws/bank/?token=<access_token>
                    # ws://host/ws/expense/?token=<access_token>
                    # ... more routes can be added here
                    # NOTE: Import moved inside to avoid AppRegistryNotReady
                ]
            )
        ),
    }
)


# Late import to avoid AppRegistryNotReady error
# Django must load models before Channels routing can resolve consumers.
def _get_ws_urlpatterns():
    """Lazy-load websocket URL patterns after Django app registry is ready."""
    from apps.consumers.routing import websocket_urlpatterns

    return websocket_urlpatterns


# Monkey-patch the URLRouter with actual patterns after app ready
from django.apps import apps


class _LazyURLRouter(URLRouter):
    """URLRouter that resolves patterns lazily after Django apps are loaded."""

    def __init__(self):
        # Will be populated after app ready
        super().__init__([])

    def resolve(self, scope):
        if not self.urlpatterns:
            self.urlpatterns = _get_ws_urlpatterns()
        return super().resolve(scope)


# Replace the websocket routing with lazy version
_ws_router = _LazyURLRouter()
application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(_ws_router),
    }
)
