from passlib.context import CryptContext
from jose import jwt
from datetime import timedelta

from src.infrastructure.db.repositories.user_repository import UserRepository
from src.core.config.settings import env_vars
from src.utils.timing import now



# Config
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository


    def verify_password(self, plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)


    def create_access_token(self, data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        expire = now() + (expires_delta or timedelta(minutes=env_vars.access_token_expire_minutes))
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, env_vars.secret_key, algorithm=env_vars.hash_algorithm)
        return encoded_jwt


    async def authenticate_user(self, username: str, password: str):
        user = await self.user_repository.get_by_username(username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

