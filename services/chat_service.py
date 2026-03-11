from sqlalchemy import and_, func, select
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
        subq = (
            select(AllowedChat.chat_id, func.max(AllowedChat.id).label('max_id'))
            .where(AllowedChat.is_active.is_(True))
            .group_by(AllowedChat.chat_id)
            .subquery()
        )
        stmt = (
            select(AllowedChat)
            .join(subq, and_(AllowedChat.chat_id == subq.c.chat_id, AllowedChat.id == subq.c.max_id))
            .order_by(AllowedChat.title)
        )
        return list((await self.session.scalars(stmt)).all())

    async def refresh_allowed_chats(self, bot) -> list[AllowedChat]:
        chats = await self.list_allowed()
        changed = False
        for chat in chats:
            try:
                tg_chat = await bot.get_chat(chat.chat_id)
            except Exception:
                if chat.is_active:
                    chat.is_active = False
                    changed = True
                continue

            title = getattr(tg_chat, 'title', None) or f'Chat {chat.chat_id}'
            if chat.title != title:
                chat.title = title
                changed = True
            if not chat.is_active:
                chat.is_active = True
                changed = True

        if changed:
            await self.session.commit()
        return await self.list_allowed()

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
