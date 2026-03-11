from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import delete_session_confirm_keyboard, history_session_actions_keyboard, sessions_keyboard
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
    await msg.answer('Выберите инвентаризацию:', reply_markup=sessions_keyboard(pairs, back='menu:main'))
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
        f"Инвентаризация #{s.id}\n"
        f"Создана: {s.created_at}\n"
        f"Завершена: {s.finished_at}\n"
        f"Позиций: {card['items_count']}\n"
        f"Лист: {s.google_sheet_url or '-'}"
    )
    await callback.message.answer(text, reply_markup=history_session_actions_keyboard(sid))
    await callback.answer()


@router.callback_query(F.data.startswith('sessdel:'))
async def request_delete_session(callback: CallbackQuery, session: AsyncSession) -> None:
    sid = int(callback.data.split(':')[1])
    card = await InventoryService(session).session_card(sid)
    if not card['session']:
        await callback.answer('Инвентаризация уже удалена.', show_alert=True)
        return
    await callback.message.answer(
        f'Удалить инвентаризацию #{sid} из истории и базы данных?',
        reply_markup=delete_session_confirm_keyboard(sid),
    )
    await callback.answer()


@router.callback_query(F.data.startswith('sessdel_confirm:'))
async def delete_session_confirm(callback: CallbackQuery, session: AsyncSession) -> None:
    sid = int(callback.data.split(':')[1])
    deleted = await InventoryService(session).delete_session(sid)
    if not deleted:
        await callback.answer('Инвентаризация не найдена.', show_alert=True)
        return
    await callback.message.answer(f'Инвентаризация #{sid} удалена из истории и базы данных.')
    await callback.answer('Удалено')
