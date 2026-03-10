from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import AllowedChat, AllowedChatTopic


class ChatService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def remember_chat(self, chat_id: int, title: str) -> None:
        chat = await self.session.scalar(select(AllowedChat).where(AllowedChat.chat_id == chat_id))
        if chat:
            chat.title = title
            chat.is_active = True
        else:
            self.session.add(AllowedChat(chat_id=chat_id, title=title, is_active=True))
        await self.session.commit()

    async def remember_topic(self, chat_id: int, thread_id: int, title: str) -> None:
        topic = await self.session.scalar(
            select(AllowedChatTopic).where(AllowedChatTopic.chat_id == chat_id, AllowedChatTopic.thread_id == thread_id)
        )
        if topic:
            topic.title = title
            topic.is_active = True
        else:
            self.session.add(AllowedChatTopic(chat_id=chat_id, thread_id=thread_id, title=title, is_active=True))
        await self.session.commit()

    async def list_allowed(self) -> list[AllowedChat]:
        return list((await self.session.scalars(select(AllowedChat).where(AllowedChat.is_active.is_(True)).order_by(AllowedChat.title))).all())

    async def list_topics(self, chat_id: int) -> list[AllowedChatTopic]:
        return list(
            (
                await self.session.scalars(
                    select(AllowedChatTopic)
                    .where(AllowedChatTopic.chat_id == chat_id, AllowedChatTopic.is_active.is_(True))
                    .order_by(AllowedChatTopic.title)
                )
            ).all()
        )

    async def get(self, chat_id: int) -> AllowedChat | None:
        return await self.session.scalar(select(AllowedChat).where(AllowedChat.chat_id == chat_id, AllowedChat.is_active.is_(True)))

    async def get_topic(self, chat_id: int, thread_id: int) -> AllowedChatTopic | None:
        return await self.session.scalar(
            select(AllowedChatTopic).where(
                AllowedChatTopic.chat_id == chat_id,
                AllowedChatTopic.thread_id == thread_id,
                AllowedChatTopic.is_active.is_(True),
            )
        )
