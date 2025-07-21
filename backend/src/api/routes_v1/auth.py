from litestar import Controller, Response, post
from litestar.di import Provide

from src.api.dependencies.auth import provide_auth_service
from src.api.dependencies.user import provide_user_repository
from src.api.schemas.auth import LoginRequest, TokenResponse
from src.application.user.services.auth_service import AuthService



class AuthController(Controller):
    @post("/login", dependencies={
        "user_repository": Provide(provide_user_repository),
        "auth_service": Provide(provide_auth_service)
    })
    async def login(self, data: LoginRequest, auth_service: AuthService) -> TokenResponse:
        user = await auth_service.authenticate_user(data.username, data.password)
        if not user:
            return Response(status_code=401, content={"detail": "Invalid credentials"})

        access_token = auth_service.create_access_token({"sub": user.username})
        return TokenResponse(access_token=access_token)

