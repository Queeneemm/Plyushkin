from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import get_settings
from db.models import User, UserRole


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def ensure_user(self, telegram_id: int, username: str | None) -> User:
        user = await self.session.scalar(select(User).where(User.telegram_id == telegram_id))
        if user:
            if username != user.username:
                user.username = username
                await self.session.commit()
            return user
        role = UserRole.admin if telegram_id == get_settings().admin_telegram_id else UserRole.user
        user = User(telegram_id=telegram_id, username=username, role=role, is_active=role == UserRole.admin)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_identifier(self, identifier: str) -> User | None:
        if identifier.isdigit():
            return await self.session.scalar(select(User).where(User.telegram_id == int(identifier)))
        uname = identifier.lstrip('@').lower()
        return await self.session.scalar(select(User).where(User.username == uname))

    async def set_role(self, user: User, role: UserRole) -> User:
        user.role = role
        user.is_active = True
        await self.session.commit()
        return user

    async def revoke_access(self, user: User) -> None:
        user.is_active = False
        await self.session.commit()
