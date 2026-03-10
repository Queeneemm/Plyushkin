from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import access_menu_keyboard, inventory_menu_keyboard, main_menu_keyboard, pool_menu_keyboard
from services.chat_service import ChatService

router = Router()


@router.message(F.text == '/start')
async def start_cmd(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer('Бот инвентаризации готов к работе. Выберите раздел:', reply_markup=main_menu_keyboard())


@router.callback_query(F.data == 'menu:main')
async def open_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer('Главное меню:', reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == 'menu:inventory')
async def open_inventory_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer('Раздел инвентарки:', reply_markup=inventory_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == 'menu:pool')
async def open_pool_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer('Раздел управления пулом:', reply_markup=pool_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == 'menu:access')
async def open_access_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer('Раздел доступов:', reply_markup=access_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == 'nav:cancel')
async def cancel_flow(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer('Действие отменено.', reply_markup=main_menu_keyboard())
    await callback.answer()


@router.message(F.chat.type.in_({'group', 'supergroup'}))
async def track_group_chat(message: Message, session: AsyncSession) -> None:
    title = message.chat.title or f'Chat {message.chat.id}'
    await ChatService(session).remember_chat(message.chat.id, title)
