from pathlib import Path

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import (
    back_keyboard,
    cancel_inventory_confirm_keyboard,
    duplicate_keyboard,
    finish_confirm_keyboard,
    item_actions_keyboard,
    items_keyboard,
    products_keyboard,
)
from bot.keyboards.main_menu import inventory_input_mode_keyboard, main_menu
from bot.states.forms import EditItemStates, InventoryStates
from config.settings import get_settings
from db.models import InventoryItem, User
from services.crm_parser import CRMExcelParser, CRMParserConfig
from services.google_sheets_service import GoogleSheetsService
from services.inventory_service import InventoryService
from services.product_service import ProductService

router = Router()

@router.message(F.text == 'Начать инвентарку / Продолжить инвентарку')
@router.callback_query(F.data == 'inv:start')
async def start_or_continue_inventory(event: Message | CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    inv = InventoryService(session)
    s = await inv.get_or_create_active(db_user.id)
    msg = event.message if isinstance(event, CallbackQuery) else event
    await state.set_state(InventoryStates.waiting_search_query)
    await msg.answer(
        f'Активная инвентарка #{s.id}. Отправьте текст (название/алиас) для добавления позиции. Для выхода нажмите «⬅️ Назад».',
        reply_markup=inventory_input_mode_keyboard(),
    )
    if isinstance(event, CallbackQuery):
        await event.answer()

@router.message(F.text == 'Внести позицию')
@router.callback_query(F.data == 'inv:add_item')
async def ask_search(event: Message | CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    msg = event.message if isinstance(event, CallbackQuery) else event
    if not await InventoryService(session).get_active_session():
        await msg.answer('Нет активной инвентарки. Сначала нажмите "Начать инвентарку / Продолжить инвентарку".')
        if isinstance(event, CallbackQuery):
            await event.answer()
        return
    await state.set_state(InventoryStates.waiting_search_query)
    await msg.answer(
        'Введите часть названия или алиас товара. Для выхода нажмите «⬅️ Назад».',
        reply_markup=inventory_input_mode_keyboard(),
    )
    if isinstance(event, CallbackQuery):
        await event.answer()

@router.message(InventoryStates.waiting_search_query, F.text != '⬅️ Назад')
async def search_product(message: Message, state: FSMContext, session: AsyncSession) -> None:
    query = (message.text or '').strip()
    products = await ProductService(session).search_active(query)
    if not products:
        await message.answer('Ничего не найдено. Попробуйте другой запрос.')
        return
    await message.answer('Выберите товар:', reply_markup=products_keyboard([(p.id, p.full_name) for p in products]))

@router.callback_query(F.data.startswith('product:'))
async def product_selected(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    product_id = int(callback.data.split(':')[1])
    active = await InventoryService(session).get_active_session()
    if not active:
        await callback.answer('Нет активной инвентарки', show_alert=True)
        return
    existing = await InventoryService(session).get_item(active.id, product_id)
    await state.update_data(product_id=product_id)
    if existing:
        await state.set_state(InventoryStates.waiting_duplicate_action)
        await callback.message.answer('Товар уже внесён. Что сделать?', reply_markup=duplicate_keyboard())
    else:
        await state.set_state(InventoryStates.waiting_quantity)
        await callback.message.answer('Введите количество:', reply_markup=back_keyboard('menu:inventory'))
    await callback.answer()

@router.callback_query(InventoryStates.waiting_duplicate_action, F.data.startswith('dup:'))
async def duplicate_action(callback: CallbackQuery, state: FSMContext) -> None:
    action = callback.data.split(':')[1]
    if action == 'cancel':
        await state.clear()
        await callback.message.answer('Отменено.')
    else:
        await state.update_data(duplicate_mode='add' if action == 'add' else 'replace')
        await state.set_state(InventoryStates.waiting_quantity)
        await callback.message.answer('Введите количество:', reply_markup=back_keyboard('menu:inventory'))
    await callback.answer()

@router.message(InventoryStates.waiting_quantity)
async def save_quantity(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        qty = float((message.text or '').replace(',', '.'))
        if qty < 0:
            raise ValueError
    except ValueError:
        await message.answer('Введите неотрицательное число.')
        return

    data = await state.get_data()
    product_id = data['product_id']
    mode = data.get('duplicate_mode', 'replace')

    active = await InventoryService(session).get_active_session()
    if not active:
        await message.answer('Активная инвентарка не найдена.')
        await state.clear()
        return
    await InventoryService(session).upsert_item(active.id, product_id, qty, mode=mode)
    await state.set_state(InventoryStates.waiting_search_query)
    await message.answer(
        'Позиция сохранена. Отправьте следующую позицию (название/алиас) или нажмите «⬅️ Назад».',
        reply_markup=inventory_input_mode_keyboard(),
    )


@router.message(InventoryStates.waiting_search_query, F.text == '⬅️ Назад')
async def leave_inventory_input_mode(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer('Вы вышли из режима внесения позиций.', reply_markup=main_menu())

@router.message(F.text == 'Показать внесённые')
@router.callback_query(F.data == 'inv:show_items')
async def show_items(event: Message | CallbackQuery, session: AsyncSession) -> None:
    msg = event.message if isinstance(event, CallbackQuery) else event
    active = await InventoryService(session).get_active_session()
    if not active:
        await msg.answer('Нет активной инвентарки.')
        if isinstance(event, CallbackQuery):
            await event.answer()
        return
    items = await InventoryService(session).list_items(active.id)
    if not items:
        await msg.answer('Пока нет внесённых позиций.')
        if isinstance(event, CallbackQuery):
            await event.answer()
        return
    text = '\n'.join([f'• {it.product.full_name}: {float(it.quantity_fact)}' for it in items[:30]])
    await msg.answer(f'Внесено:\n{text}')
    await msg.answer('Выберите позицию для изменения/удаления:', reply_markup=items_keyboard([(it.id, it.product.full_name) for it in items[:20]]))
    if isinstance(event, CallbackQuery):
        await event.answer()

@router.callback_query(F.data.startswith('item:'))
async def show_item_actions(callback: CallbackQuery, session: AsyncSession) -> None:
    item_id = int(callback.data.split(':')[1])
    await callback.message.answer('Действия с позицией:', reply_markup=item_actions_keyboard(item_id))
    await callback.answer()

@router.callback_query(F.data.startswith('item_edit:'))
async def edit_item_start(callback: CallbackQuery, state: FSMContext) -> None:
    item_id = int(callback.data.split(':')[1])
    await state.update_data(edit_item_id=item_id)
    await state.set_state(EditItemStates.waiting_new_quantity)
    await callback.message.answer('Введите новое количество:', reply_markup=back_keyboard('inv:show_items'))
    await callback.answer()

@router.message(EditItemStates.waiting_new_quantity)
async def edit_item_finish(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        qty = float((message.text or '').replace(',', '.'))
    except ValueError:
        await message.answer('Введите число.')
        return
    data = await state.get_data()
    item = await session.get(InventoryItem, data['edit_item_id'])
    if not item:
        await message.answer('Позиция не найдена.')
        await state.clear()
        return
    item.quantity_fact = qty
    await session.commit()
    await message.answer('Количество обновлено.')
    await state.clear()

@router.callback_query(F.data.startswith('item_del:'))
async def delete_item(callback: CallbackQuery, session: AsyncSession) -> None:
    item_id = int(callback.data.split(':')[1])
    await InventoryService(session).delete_item(item_id)
    await callback.message.answer('Позиция удалена.')
    await callback.answer()

@router.message(F.text == 'Отменить инвентарку')
@router.callback_query(F.data == 'inv:cancel')
async def cancel_inventory_start(event: Message | CallbackQuery, session: AsyncSession) -> None:
    msg = event.message if isinstance(event, CallbackQuery) else event
    if not await InventoryService(session).get_active_session():
        await msg.answer('Нет активной инвентарки.')
        if isinstance(event, CallbackQuery):
            await event.answer()
        return
    await msg.answer('Точно отменить текущую инвентарку? Все внесённые позиции в ней будут недоступны.', reply_markup=cancel_inventory_confirm_keyboard())
    if isinstance(event, CallbackQuery):
        await event.answer()

@router.callback_query(F.data == 'invcancel:yes')
async def cancel_inventory_confirmed(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    cancelled = await InventoryService(session).cancel_active_session()
    if cancelled:
        await callback.message.answer(f'Инвентарка #{cancelled.id} отменена.')
    else:
        await callback.message.answer('Нет активной инвентарки.')
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == 'invcancel:no')
async def cancel_inventory_rejected(callback: CallbackQuery) -> None:
    await callback.message.answer('Отмена инвентарки не выполнена.')
    await callback.answer()


@router.message(F.text == 'Завершить инвентарку')
@router.callback_query(F.data == 'inv:finish')
async def finish_inventory(event: Message | CallbackQuery, session: AsyncSession) -> None:
    msg = event.message if isinstance(event, CallbackQuery) else event
    if not await InventoryService(session).get_active_session():
        await msg.answer('Нет активной инвентарки.')
        if isinstance(event, CallbackQuery):
            await event.answer()
        return
    await msg.answer('Подтвердите завершение и загрузку CRM файла.', reply_markup=finish_confirm_keyboard())
    if isinstance(event, CallbackQuery):
        await event.answer()

@router.callback_query(F.data == 'finish:yes')
async def finish_confirmed(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(InventoryStates.waiting_finish_crm_file)
    await callback.message.answer('Отправьте xlsx файл CRM документом.', reply_markup=back_keyboard('menu:inventory'))
    await callback.answer()

@router.callback_query(F.data == 'finish:no')
async def finish_cancelled(callback: CallbackQuery) -> None:
    await callback.message.answer('Завершение отменено.')
    await callback.answer()

@router.message(InventoryStates.waiting_finish_crm_file, F.document)
async def process_finish_file(message: Message, state: FSMContext, session: AsyncSession) -> None:
    doc = message.document
    if not doc.file_name.lower().endswith('.xlsx'):
        await message.answer('Нужен именно .xlsx файл.')
        return

    path = Path('tmp')
    path.mkdir(exist_ok=True)
    local = path / f'{doc.file_unique_id}.xlsx'
    await message.bot.download(doc, destination=local)

    settings = get_settings()
    parser = CRMExcelParser(CRMParserConfig(settings.crm_name_column, settings.crm_stock_column, settings.crm_header_row))
    crm_map = parser.parse_stock(local)

    inv = InventoryService(session)
    active = await inv.get_active_session()
    if not active:
        await message.answer('Активная инвентарка не найдена.')
        await state.clear()
        return

    fact_map = await inv.fact_map(active.id)
    all_product_ids = list(fact_map.keys())

    product_service = ProductService(session)
    for crm_name in crm_map.keys():
        products = await product_service.search_active(crm_name, limit=1)
        if products and products[0].full_name.lower() == crm_name.lower():
            all_product_ids.append(products[0].id)

    products = await inv.products_by_ids(list(set(all_product_ids)))
    rows: list[tuple[str, float, float]] = []

    for pid, product in sorted(products.items(), key=lambda x: x[1].full_name.lower()):
        crm_qty = crm_map.get(product.full_name, 0)
        fact_qty = fact_map.get(pid, 0)
        rows.append((product.full_name, crm_qty, fact_qty))

    gs = GoogleSheetsService(settings.google_credentials_json, settings.google_spreadsheet_id, settings.template_sheet_name)
    _, tab_name, url = gs.create_inventory_sheet()
    if rows:
        gs.write_inventory_rows(tab_name, rows)

    await inv.finish_session(active.id, url, tab_name)
    await message.answer(f'Инвентарка завершена. Лист: {url}\nПозиций: {len(rows)}')
    await state.clear()
