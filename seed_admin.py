import asyncio
from database import engine, Base, SessionLocal
from models import User
from auth import hash_password


async def create_admin():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        admin = User(
            email="john@admin.com",
            username="admin",
            hashed_password=hash_password("admin123"),
            is_admin=True,
        )
        db.add(admin)
        await db.commit()
        print("Admin credated successfully")


asyncio.run(create_admin())
