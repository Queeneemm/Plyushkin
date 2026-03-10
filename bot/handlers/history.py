from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import sessions_keyboard
from services.inventory_service import InventoryService

router = Router()


@router.message(F.text == 'История инвентарок')
@router.callback_query(F.data == 'menu:history')
async def history_list(event: Message | CallbackQuery, session: AsyncSession) -> None:
    msg = event.message if isinstance(event, CallbackQuery) else event
    sessions = await InventoryService(session).history()
    if not sessions:
        await msg.answer('История пуста.')
        if isinstance(event, CallbackQuery):
            await event.answer()
        return
    pairs = [(s.id, f"#{s.id} {s.finished_at:%Y-%m-%d %H:%M}") for s in sessions if s.finished_at]
    await msg.answer('Выберите инвентарку:', reply_markup=sessions_keyboard(pairs, back='menu:main'))
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.callback_query(F.data.startswith('sess:'))
async def history_card(callback: CallbackQuery, session: AsyncSession) -> None:
    sid = int(callback.data.split(':')[1])
    card = await InventoryService(session).session_card(sid)
    s = card['session']
    if not s:
        await callback.answer('Не найдено', show_alert=True)
        return
    text = (
        f"Инвентарка #{s.id}\n"
        f"Создана: {s.created_at}\n"
        f"Завершена: {s.finished_at}\n"
        f"Позиций: {card['items_count']}\n"
        f"Лист: {s.google_sheet_url or '-'}"
    )
    await callback.message.answer(text)
    await callback.answer()
