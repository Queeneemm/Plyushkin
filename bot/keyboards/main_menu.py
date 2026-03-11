from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Начать инвентарку / Продолжить инвентарку')],
            [KeyboardButton(text='Внести позицию'), KeyboardButton(text='Показать внесённые')],
            [KeyboardButton(text='Завершить инвентарку')],
            [KeyboardButton(text='История инвентарок')],
            [KeyboardButton(text='Управление пулом')],
            [KeyboardButton(text='Доступы')],
            [KeyboardButton(text='Отправить сводку')],
        ],
        resize_keyboard=True,
    )


def inventory_input_mode_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='⬅️ Назад')]],
        resize_keyboard=True,
    )
