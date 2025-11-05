from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db import close_old_connections
from asgiref.sync import sync_to_async

class JWTAuthMiddleware(BaseMiddleware):
    """Custom middleware that takes a JWT token from the query string `token` and
    authenticates the user for the scope.
    """
    async def __call__(self, scope, receive, send):
        # Close old DB connections to prevent usage in threads
        close_old_connections()
        query_string = scope.get('query_string', b'').decode()
        token = None
        if query_string:
            try:
                import urllib.parse
                qs = urllib.parse.parse_qs(query_string)
                token = qs.get('token', [None])[0]
            except Exception:
                token = None

        if token:
            try:
                jwt_auth = JWTAuthentication()
                validated = jwt_auth.get_validated_token(token)
                user = await sync_to_async(jwt_auth.get_user)(validated)
                scope['user'] = user
            except Exception:
                scope['user'] = AnonymousUser()
        else:
            scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)
