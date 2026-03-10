from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import role_keyboard
from bot.states.forms import AccessStates
from db.models import User, UserRole
from services.auth_service import AuthService

router = Router()


def _is_admin(user: User) -> bool:
    return user.role == UserRole.admin and user.is_active


@router.message(F.text == 'Доступы')
async def access_menu(message: Message, db_user: User) -> None:
    if not _is_admin(db_user):
        await message.answer('Раздел доступен только администратору.')
        return
    await message.answer('Команды:\n/access_add\n/access_revoke <@username|telegram_id>')


@router.message(F.text == '/access_add')
async def add_user_start(message: Message, state: FSMContext, db_user: User) -> None:
    if not _is_admin(db_user):
        await message.answer('Только для админа.')
        return
    await state.set_state(AccessStates.waiting_user_identifier)
    await message.answer('Введите @username или telegram_id пользователя:')


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
        await callback.message.answer(f'Доступ выдан: {user.telegram_id}, роль={role.value}.')
    await callback.answer()
    await state.clear()


@router.message(F.text.startswith('/access_revoke'))
async def revoke_access(message: Message, session: AsyncSession, db_user: User) -> None:
    if not _is_admin(db_user):
        await message.answer('Только для админа.')
        return
    parts = (message.text or '').split(maxsplit=1)
    if len(parts) != 2:
        await message.answer('Использование: /access_revoke <@username|telegram_id>')
        return
    auth = AuthService(session)
    user = await auth.get_by_identifier(parts[1])
    if not user:
        await message.answer('Пользователь не найден.')
        return
    await auth.revoke_access(user)
    await message.answer('Доступ отозван.')
