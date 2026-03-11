from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='📦 Инвентарка', callback_data='menu:inventory')],
            [InlineKeyboardButton(text='🗂 Управление пулом', callback_data='menu:pool')],
            [InlineKeyboardButton(text='📜 История инвентарок', callback_data='menu:history')],
            [InlineKeyboardButton(text='📤 Отправить сводку', callback_data='menu:summary')],
            [InlineKeyboardButton(text='🔐 Доступы', callback_data='menu:access')],
        ]
    )

def inventory_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Начать / Продолжить', callback_data='inv:start')],
            [InlineKeyboardButton(text='Внести позицию', callback_data='inv:add_item')],
            [InlineKeyboardButton(text='Показать внесённые', callback_data='inv:show_items')],
            [InlineKeyboardButton(text='Завершить инвентарку', callback_data='inv:finish')],
            [InlineKeyboardButton(text='Отменить инвентарку', callback_data='inv:cancel')],
            [InlineKeyboardButton(text='⬅️ Назад', callback_data='menu:main')],
        ]
    )

def pool_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Импорт из CRM', callback_data='pool:import')],
            [InlineKeyboardButton(text='Добавить вручную', callback_data='pool:add')],
            [InlineKeyboardButton(text='Поиск', callback_data='pool:search')],
            [InlineKeyboardButton(text='Архивировать', callback_data='pool:archive')],
            [InlineKeyboardButton(text='Восстановить', callback_data='pool:restore')],
            [InlineKeyboardButton(text='Переименовать', callback_data='pool:rename')],
            [InlineKeyboardButton(text='Алиасы', callback_data='pool:aliases')],
            [InlineKeyboardButton(text='Выгрузить базу (Excel)', callback_data='pool:export')],
            [InlineKeyboardButton(text='⬅️ Назад', callback_data='menu:main')],
        ]
    )

def access_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Выдать доступ', callback_data='access:add')],
            [InlineKeyboardButton(text='Отозвать доступ', callback_data='access:revoke')],
            [InlineKeyboardButton(text='⬅️ Назад', callback_data='menu:main')],
        ]
    )

def back_keyboard(target: str = 'menu:main') -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='⬅️ Назад', callback_data=target)]])

def products_keyboard(items: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=name[:60], callback_data=f'product:{pid}')] for pid, name in items]
    rows.append([InlineKeyboardButton(text='⬅️ Назад', callback_data='menu:inventory')])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def duplicate_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Заменить', callback_data='dup:replace'),
                InlineKeyboardButton(text='Прибавить', callback_data='dup:add'),
                InlineKeyboardButton(text='Отмена', callback_data='dup:cancel'),
            ],
            [InlineKeyboardButton(text='⬅️ Назад', callback_data='menu:inventory')],
        ]
    )

def cancel_inventory_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Да, отменить', callback_data='invcancel:yes'),
                InlineKeyboardButton(text='Нет', callback_data='invcancel:no'),
            ],
            [InlineKeyboardButton(text='⬅️ Назад', callback_data='menu:inventory')],
        ]
    )


def finish_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Да, завершить', callback_data='finish:yes'),
                InlineKeyboardButton(text='Отмена', callback_data='finish:no'),
            ],
            [InlineKeyboardButton(text='⬅️ Назад', callback_data='menu:inventory')],
        ]
    )

def items_keyboard(items: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=name[:60], callback_data=f'item:{iid}')] for iid, name in items]
    rows.append([InlineKeyboardButton(text='⬅️ Назад', callback_data='menu:inventory')])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def item_actions_keyboard(item_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Изменить количество', callback_data=f'item_edit:{item_id}'),
                InlineKeyboardButton(text='Удалить', callback_data=f'item_del:{item_id}'),
            ],
            [InlineKeyboardButton(text='⬅️ Назад', callback_data='inv:show_items')],
        ]
    )

def role_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='admin', callback_data='role:admin'), InlineKeyboardButton(text='user', callback_data='role:user')],
            [InlineKeyboardButton(text='⬅️ Назад', callback_data='menu:access')],
        ]
    )

def chats_keyboard(chats: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=title[:60], callback_data=f'chat:{cid}')] for cid, title in chats]
    rows.append([InlineKeyboardButton(text='⬅️ Назад', callback_data='menu:summary')])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def topics_keyboard(chat_id: int, topics: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=title[:60], callback_data=f'topic:{chat_id}:{tid}')] for tid, title in topics]
    rows.append([InlineKeyboardButton(text='В общий чат', callback_data=f'topic:{chat_id}:0')])
    rows.append([InlineKeyboardButton(text='⬅️ Назад', callback_data='menu:summary')])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def sessions_keyboard(sessions: list[tuple[int, str]], prefix: str = 'sess', back: str = 'menu:main') -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=label, callback_data=f'{prefix}:{sid}')] for sid, label in sessions]
    rows.append([InlineKeyboardButton(text='⬅️ Назад', callback_data=back)])
    return InlineKeyboardMarkup(inline_keyboard=rows)
