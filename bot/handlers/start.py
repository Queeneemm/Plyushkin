from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.main_menu import main_menu
from services.chat_service import ChatService

router = Router()


@router.message(CommandStart())
async def start_cmd(message: Message) -> None:
    await message.answer('Бот инвентаризации готов к работе.', reply_markup=main_menu())


@router.message(F.chat.type.in_({'group', 'supergroup'}))
async def track_group_chat(message: Message, session: AsyncSession) -> None:
    title = message.chat.title or f'Chat {message.chat.id}'
    await ChatService(session).remember_chat(message.chat.id, title)
