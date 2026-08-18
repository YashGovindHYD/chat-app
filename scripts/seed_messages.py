"""Seed a group conversation with members and a few messages, using the users from seed_users.py."""

import asyncio

from sqlalchemy import select

from db.database import async_session
from models.models import Conversation, ConversationMember, Message, User

TEST_MESSAGES = [
    ("alice@test.local", "hey everyone, welcome to the group!"),
    ("bob@test.local", "hey alice, glad to be here"),
    ("carol@test.local", "hi all!"),
    ("alice@test.local", "let's plan the weekend trip here"),
    ("bob@test.local", "sounds good, I'm in"),
]


async def seed():
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.email.in_({email for email, _ in TEST_MESSAGES}))
        )
        users_by_email = {user.email: user for user in result.scalars().all()}
        if len(users_by_email) < 3:
            print("Run scripts/seed_users.py first — missing test users.")
            return

        owner = users_by_email["alice@test.local"]
        conversation = Conversation(name="Weekend Trip", type="group-chat", owner=owner.id)
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)

        members = [
            ConversationMember(role="member", conversation_id=conversation.id, user_id=user.id)
            for user in users_by_email.values()
        ]
        session.add_all(members)

        messages = [
            Message(
                content=content,
                user_id=users_by_email[email].id,
                conversation_id=conversation.id,
            )
            for email, content in TEST_MESSAGES
        ]
        session.add_all(messages)
        await session.commit()

        print(f"conversation {conversation.id}: {conversation.name}")
        for message in messages:
            await session.refresh(message)
            print(f"  {message.id}: {message.content!r}")


if __name__ == "__main__":
    asyncio.run(seed())
