from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import chats_keyboard, sessions_keyboard
from bot.states.forms import SummaryStates
from services.chat_service import ChatService
from services.inventory_service import InventoryService

router = Router()


@router.message(F.text == 'Отправить сводку')
@router.callback_query(F.data == 'menu:summary')
async def summary_start(event: Message | CallbackQuery, session: AsyncSession) -> None:
    msg = event.message if isinstance(event, CallbackQuery) else event
    sessions = await InventoryService(session).history(limit=10)
    if not sessions:
        await msg.answer('Нет завершённых инвентарок.')
        if isinstance(event, CallbackQuery):
            await event.answer()
        return
    await msg.answer(
        'Выберите инвентарку для отправки сводки:',
        reply_markup=sessions_keyboard([(s.id, f"#{s.id} {s.finished_at:%Y-%m-%d}") for s in sessions if s.finished_at], prefix='sumsess', back='menu:main'),
    )
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.callback_query(F.data.startswith('sumsess:'))
async def choose_chat(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    sid = int(callback.data.split(':')[1])
    await state.set_state(SummaryStates.waiting_chat_choice)
    await state.update_data(summary_session_id=sid)
    chats = await ChatService(session).list_allowed()
    if not chats:
        await callback.message.answer('Нет доступных чатов. Добавьте бота в чат и отправьте там сообщение.')
        await callback.answer()
        return
    await callback.message.answer('Выберите чат:', reply_markup=chats_keyboard([(c.chat_id, c.title) for c in chats]))
    await callback.answer()


@router.callback_query(SummaryStates.waiting_chat_choice, F.data.startswith('chat:'))
async def send_summary_callback(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    chat_id = int(callback.data.split(':')[1])
    data = await state.get_data()
    sid = data.get('summary_session_id')
    if not sid:
        await callback.message.answer('Сессия не выбрана.')
        await callback.answer()
        return

    chat = await ChatService(session).get(chat_id)
    if not chat:
        await callback.message.answer('Чат недоступен.')
        await callback.answer()
        return

    card = await InventoryService(session).session_card(sid)
    s = card['session']
    if not s:
        await callback.message.answer('Инвентарка не найдена.')
        await callback.answer()
        return

    text = (
        f"Сводка по инвентарке #{s.id}\n"
        f"Дата: {s.finished_at:%Y-%m-%d %H:%M}\n"
        f"Позиций: {card['items_count']}\n"
        f"Ссылка: {s.google_sheet_url or '-'}\n"
        f"Статус: отчёт сформирован"
    )
    try:
        await callback.message.bot.send_message(chat_id=chat_id, text=text)
        await callback.message.answer('Сводка отправлена.')
    except Exception:
        await callback.message.answer('Не удалось отправить в чат. Проверьте права бота.')
    await state.clear()
    await callback.answer()


@router.message(F.text.startswith('/send_summary'))
async def send_summary_cmd(message: Message, session: AsyncSession) -> None:
    parts = (message.text or '').split()
    if len(parts) != 3:
        await message.answer('Использование: /send_summary <session_id> <chat_id>')
        return
    sid, chat_id = int(parts[1]), int(parts[2])
    chat = await ChatService(session).get(chat_id)
    if not chat:
        await message.answer('Чат недоступен.')
        return
    card = await InventoryService(session).session_card(sid)
    s = card['session']
    if not s:
        await message.answer('Инвентарка не найдена.')
        return
    text = (
        f"Сводка по инвентарке #{s.id}\n"
        f"Дата: {s.finished_at:%Y-%m-%d %H:%M}\n"
        f"Позиций: {card['items_count']}\n"
        f"Ссылка: {s.google_sheet_url or '-'}\n"
        f"Статус: отчёт сформирован"
    )
    try:
        await message.bot.send_message(chat_id=chat_id, text=text)
        await message.answer('Сводка отправлена.')
    except Exception:
        await message.answer('Не удалось отправить в чат. Проверьте права бота.')
