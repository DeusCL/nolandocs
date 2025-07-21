from litestar.connection import Request
from litestar import Response

from src.infrastructure.db.repositories.user_repository import UserRepository
from src.application.user.services.auth_service import AuthService



async def provide_auth_service(user_repository: UserRepository) -> AuthService:
    return AuthService(user_repository)


def require_role(required_roles: list[str]):
    def decorator(handler):
        async def wrapper(request: Request, *args, **kwargs):
            user_role = request.scope.get("role")
            if user_role not in required_roles:
                return Response(status_code=403, content={"detail": "Forbidden"})
            return await handler(request, *args, **kwargs)
        return wrapper
    return decorator
