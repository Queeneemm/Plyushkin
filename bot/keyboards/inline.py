from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def products_keyboard(items: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=name[:60], callback_data=f'product:{pid}')] for pid, name in items]
    )


def duplicate_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text='Заменить', callback_data='dup:replace'),
            InlineKeyboardButton(text='Прибавить', callback_data='dup:add'),
            InlineKeyboardButton(text='Отмена', callback_data='dup:cancel'),
        ]]
    )


def finish_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text='Да, завершить', callback_data='finish:yes'),
            InlineKeyboardButton(text='Отмена', callback_data='finish:no'),
        ]]
    )


def items_keyboard(items: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=name[:60], callback_data=f'item:{iid}')] for iid, name in items]
    )


def item_actions_keyboard(item_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text='Изменить количество', callback_data=f'item_edit:{item_id}'),
            InlineKeyboardButton(text='Удалить', callback_data=f'item_del:{item_id}'),
        ]]
    )


def role_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='admin', callback_data='role:admin'), InlineKeyboardButton(text='user', callback_data='role:user')]]
    )


def chats_keyboard(chats: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=title[:60], callback_data=f'chat:{cid}')] for cid, title in chats]
    )


def sessions_keyboard(sessions: list[tuple[int, str]], prefix: str = 'sess') -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=label, callback_data=f'{prefix}:{sid}')] for sid, label in sessions]
    )
