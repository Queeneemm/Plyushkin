# Telegram Inventory Bot (aiogram 3 + SQLAlchemy 2)

Production-ready MVP бота для инвентаризации товаров.

## Возможности
- Авторизация и роли (`admin`, `user`) с отзывом доступа.
- Пул товаров: импорт из CRM xlsx, ручное добавление, редактирование, архив/восстановление.
- Одна активная инвентарка одновременно.
- Внесение факта по поиску (подстрока + алиасы, регистронезависимо).
- Повторное внесение товара: заменить / прибавить.
- Редактирование и удаление внесённых позиций.
- Завершение инвентарки с загрузкой CRM xlsx.
- Формирование листа в Google Sheets на базе листа-шаблона `Шаблон`.
- История завершённых инвентаризаций.
- Отправка краткой сводки в разрешённые чаты.

## Структура
- `bot/` — aiogram app, handlers, FSM, keyboards, middlewares
- `db/` — SQLAlchemy модели, engine, init
- `services/` — бизнес-логика (CRM parser, Google Sheets, inventory и т.д.)
- `config/` — pydantic-settings

## Запуск
1. Python 3.11+
2. Установить зависимости:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
3. Создать `.env` из `.env.example` и заполнить значения.
4. Запустить:
```bash
python -m bot.main
```

## Google Service Account
1. В Google Cloud включите Google Sheets API.
2. Создайте service account и скачайте JSON credentials.
3. Укажите путь в `.env` (`GOOGLE_CREDENTIALS_JSON`).
4. Откройте целевую Google-таблицу и выдайте доступ service account email как Editor.
5. Укажите `GOOGLE_SPREADSHEET_ID` и `TEMPLATE_SHEET_NAME`.

## CRM xlsx
По умолчанию бот ждёт колонки:
- `Название`
- `Ост. на складе`

Изменяется в `.env` переменными:
- `CRM_NAME_COLUMN`
- `CRM_STOCK_COLUMN`
- `CRM_HEADER_ROW`

## Основной UX
- `/start` — открывает inline-меню (кнопки под сообщением бота).
- Основные разделы доступны из кнопок без обязательного ввода slash-команд.
- Во всех пошаговых сценариях есть кнопка `Назад` для выхода из режима.

## Команды управления пулом
- `/pool_import`
- `/pool_add`
- `/pool_search <текст>`
- `/pool_archive <id>`
- `/pool_restore <id>`
- `/pool_rename <id> <новое имя>`
- `/pool_aliases <id> <alias1,alias2>`
- Выгрузка базы в Excel: кнопка `Управление пулом` → `Выгрузить базу (Excel)`.

## Команды доступов
- `/access_add`
- `/access_revoke <@username|telegram_id>`

> Пользователь должен хотя бы раз написать боту `/start`, чтобы попасть в таблицу `users`.

## Отправка сводки
- `Отправить сводку` → выбрать сессию.
- В группах/чатах бот автоматически запоминает `chat_id` при любых сообщениях.
- Затем отправка: `/send_summary <session_id> <chat_id>`.
