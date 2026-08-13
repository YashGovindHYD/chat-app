"""Seed a few test users directly into the db, bypassing the OTP/email signup flow."""

import asyncio

from db.database import async_session
from models.models import User

TEST_USERS = [
    {"email": "alice@test.local", "name": "Alice"},
    {"email": "bob@test.local", "name": "Bob"},
    {"email": "carol@test.local", "name": "Carol"},
]


async def seed():
    async with async_session() as session:
        users = [User(**data) for data in TEST_USERS]
        session.add_all(users)
        await session.commit()
        for user in users:
            await session.refresh(user)
            print(f"{user.id}: {user.name} <{user.email}>")


if __name__ == "__main__":
    asyncio.run(seed())
