from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.db.repositories.user_repository import UserRepository


async def provide_user_repository(db: AsyncSession) -> UserRepository:
    return UserRepository(db)




