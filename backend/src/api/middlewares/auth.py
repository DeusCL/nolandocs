from litestar.types import ASGIApp, Scope, Receive, Send
from jose import jwt, JWTError

from src.core.config.settings import env_vars



class AuthMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] == "http":
            headers = dict(scope["headers"])
            auth_header = headers.get(b"authorization")
            if auth_header:
                token = auth_header.decode().split(" ")[1]
                try:
                    payload = jwt.decode(token, env_vars.secret_key, algorithms=[env_vars.hash_algorithm])
                    scope["user"] = payload.get("sub")
                    scope["role"] = payload.get("role")
                except JWTError:
                    scope["user"] = None
                    scope["role"] = None
            else:
                scope["user"] = None
                scope["role"] = None

        return await self.app(scope, receive, send)


