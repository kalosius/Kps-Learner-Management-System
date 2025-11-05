"""
ASGI config for kps project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kps.settings')

# import the Django ASGI application for HTTP
django_asgi_app = get_asgi_application()

# import our websocket routes and a simple JWT auth middleware
from school import routing as school_routing
from school.middleware import JWTAuthMiddleware


application = ProtocolTypeRouter({
	"http": django_asgi_app,
	"websocket": JWTAuthMiddleware(URLRouter(school_routing.websocket_urlpatterns)),
})
