from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import chats_keyboard, sessions_keyboard, topics_keyboard
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
async def choose_topic(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    chat_id = int(callback.data.split(':')[1])
    chat = await ChatService(session).get(chat_id)
    if not chat:
        await callback.message.answer('Чат недоступен.')
        await callback.answer()
        return

    topics = await ChatService(session).list_topics(chat_id)
    if not topics:
        await send_summary(callback, session, state, chat_id, None)
        return

    await state.set_state(SummaryStates.waiting_topic_choice)
    await state.update_data(summary_chat_id=chat_id)
    await callback.message.answer('Выберите топик для отправки:', reply_markup=topics_keyboard(chat_id, [(t.thread_id, t.title) for t in topics]))
    await callback.answer()


@router.callback_query(SummaryStates.waiting_topic_choice, F.data.startswith('topic:'))
async def send_summary_with_topic(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    _, chat_id_raw, thread_id_raw = callback.data.split(':')
    chat_id = int(chat_id_raw)
    thread_id = int(thread_id_raw)
    message_thread_id = None if thread_id == 0 else thread_id

    if message_thread_id is not None:
        topic = await ChatService(session).get_topic(chat_id, message_thread_id)
        if not topic:
            await callback.message.answer('Топик недоступен.')
            await callback.answer()
            return

    await send_summary(callback, session, state, chat_id, message_thread_id)


async def send_summary(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
    chat_id: int,
    message_thread_id: int | None,
) -> None:
    data = await state.get_data()
    sid = data.get('summary_session_id')
    if not sid:
        await callback.message.answer('Сессия не выбрана.')
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
        kwargs = {'chat_id': chat_id, 'text': text}
        if message_thread_id is not None:
            kwargs['message_thread_id'] = message_thread_id
        await callback.message.bot.send_message(**kwargs)
        await callback.message.answer('Сводка отправлена.')
    except Exception as exc:
        await callback.message.answer(f'Не удалось отправить в чат: {exc}')
    await state.clear()
    await callback.answer()


@router.message(F.text.startswith('/send_summary'))
async def send_summary_cmd(message: Message, session: AsyncSession) -> None:
    parts = (message.text or '').split()
    if len(parts) not in {3, 4}:
        await message.answer('Использование: /send_summary <session_id> <chat_id> [thread_id]')
        return
    sid, chat_id = int(parts[1]), int(parts[2])
    message_thread_id = int(parts[3]) if len(parts) == 4 else None

    chat = await ChatService(session).get(chat_id)
    if not chat:
        await message.answer('Чат недоступен.')
        return

    if message_thread_id is not None:
        topic = await ChatService(session).get_topic(chat_id, message_thread_id)
        if not topic:
            await message.answer('Топик недоступен.')
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
        kwargs = {'chat_id': chat_id, 'text': text}
        if message_thread_id is not None:
            kwargs['message_thread_id'] = message_thread_id
        await message.bot.send_message(**kwargs)
        await message.answer('Сводка отправлена.')
    except Exception as exc:
        await message.answer(f'Не удалось отправить в чат: {exc}')
