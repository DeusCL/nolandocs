import asyncio

from passlib.context import CryptContext

from src.infrastructure.db.session import get_db_session
from src.infrastructure.db.models.user import User



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_admin():
    async with get_db_session() as session:
        # Verificar si ya existe un admin
        result = await session.execute(
            User.__table__.select().where(User.username == "admin")
        )
        admin = result.first()
        if admin:
            print("Admin ya existe.")
            return

        hashed_password = pwd_context.hash("adminpasswordseguro")

        new_admin = User(
            email="admin@example.com",
            username="admin",
            hashed_password=hashed_password,
            role="admin",
            is_active=True
        )

        session.add(new_admin)
        await session.commit()
        print("Admin creado con éxito.")


if __name__ == "__main__":
    asyncio.run(seed_admin())
