from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import access_menu_keyboard, back_keyboard, role_keyboard
from bot.states.forms import AccessStates
from db.models import User, UserRole
from services.auth_service import AuthService

router = Router()


def _is_admin(user: User) -> bool:
    return user.role == UserRole.admin and user.is_active


@router.message(F.text == 'Доступы')
@router.callback_query(F.data == 'menu:access')
async def access_menu(event: Message | CallbackQuery, db_user: User) -> None:
    msg = event.message if isinstance(event, CallbackQuery) else event
    if not _is_admin(db_user):
        await msg.answer('Раздел доступен только администратору.')
        if isinstance(event, CallbackQuery):
            await event.answer()
        return
    await msg.answer('Управление доступами:', reply_markup=access_menu_keyboard())
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.message(F.text == '/access_add')
@router.callback_query(F.data == 'access:add')
async def add_user_start(event: Message | CallbackQuery, state: FSMContext, db_user: User) -> None:
    msg = event.message if isinstance(event, CallbackQuery) else event
    if not _is_admin(db_user):
        await msg.answer('Только для админа.')
        if isinstance(event, CallbackQuery):
            await event.answer()
        return
    await state.set_state(AccessStates.waiting_user_identifier)
    await msg.answer('Введите @username или telegram_id пользователя:', reply_markup=back_keyboard('menu:access'))
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.message(AccessStates.waiting_user_identifier)
async def add_user_identifier(message: Message, state: FSMContext) -> None:
    await state.update_data(identifier=(message.text or '').strip())
    await state.set_state(AccessStates.waiting_user_role)
    await message.answer('Выберите роль:', reply_markup=role_keyboard())


@router.callback_query(AccessStates.waiting_user_role, F.data.startswith('role:'))
async def add_user_finish(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    role = UserRole.admin if callback.data.endswith('admin') else UserRole.user
    data = await state.get_data()
    auth = AuthService(session)
    user = await auth.get_by_identifier(data['identifier'])
    if not user:
        await callback.message.answer('Пользователь не найден в базе. Он должен хотя бы раз написать боту /start.')
    else:
        await auth.set_role(user, role)
        await callback.message.answer(f'Доступ выдан: {user.telegram_id}, роль={role.value}.', reply_markup=access_menu_keyboard())
    await callback.answer()
    await state.clear()


@router.callback_query(F.data == 'access:revoke')
async def revoke_access_start(callback: CallbackQuery, state: FSMContext, db_user: User) -> None:
    if not _is_admin(db_user):
        await callback.message.answer('Только для админа.')
        await callback.answer()
        return
    await state.set_state(AccessStates.waiting_revoke_identifier)
    await callback.message.answer('Введите @username или telegram_id для отзыва доступа:', reply_markup=back_keyboard('menu:access'))
    await callback.answer()


@router.message(AccessStates.waiting_revoke_identifier)
@router.message(F.text.startswith('/access_revoke'))
async def revoke_access(message: Message, session: AsyncSession, db_user: User, state: FSMContext) -> None:
    if not _is_admin(db_user):
        await message.answer('Только для админа.')
        return
    if await state.get_state() == AccessStates.waiting_revoke_identifier.state:
        identifier = (message.text or '').strip()
    else:
        parts = (message.text or '').split(maxsplit=1)
        identifier = parts[1] if len(parts) == 2 else ''
    if not identifier:
        await message.answer('Нужен @username или telegram_id.')
        return
    auth = AuthService(session)
    user = await auth.get_by_identifier(identifier)
    if not user:
        await message.answer('Пользователь не найден.')
        return
    await auth.revoke_access(user)
    await message.answer('Доступ отозван.', reply_markup=access_menu_keyboard())
    await state.clear()
