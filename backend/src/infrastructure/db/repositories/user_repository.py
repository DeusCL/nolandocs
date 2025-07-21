from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.infrastructure.db.models.user import User



class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db


    async def get_by_username(self, username: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.username == username)
        )

        return result.scalar_one_or_none()

