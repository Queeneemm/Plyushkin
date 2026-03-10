from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from db.models import UserRole
from services.auth_service import AuthService


class AccessMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        session = data['session']
        auth = AuthService(session)

        tg_user = event.from_user if isinstance(event, (Message, CallbackQuery)) else None
        if not tg_user:
            return await handler(event, data)

        user = await auth.ensure_user(tg_user.id, (tg_user.username or '').lower() or None)
        data['db_user'] = user
        if not user.is_active and user.role != UserRole.admin:
            if isinstance(event, Message):
                await event.answer('Доступ закрыт. Обратитесь к администратору.')
            elif isinstance(event, CallbackQuery):
                await event.answer('Доступ закрыт', show_alert=True)
            return
        return await handler(event, data)
