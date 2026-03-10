from pathlib import Path
from tempfile import NamedTemporaryFile

from openpyxl import Workbook

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import back_keyboard, pool_menu_keyboard
from bot.states.forms import PoolStates
from config.settings import get_settings
from db.models import Product
from services.crm_parser import CRMExcelParser, CRMParserConfig
from services.product_service import ProductService

router = Router()


def _build_pool_export(products: list[Product]) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = 'Товары'
    ws.append(['ID', 'Наименование', 'Статус', 'Источник', 'Алиасы'])

    for product in products:
        aliases = ', '.join(alias.alias for alias in product.aliases)
        ws.append(
            [
                product.id,
                product.full_name,
                'Активен' if product.is_active else 'Архив',
                product.created_from.value,
                aliases,
            ]
        )

    with NamedTemporaryFile(prefix='pool_export_', suffix='.xlsx', delete=False) as tmp:
        export_path = Path(tmp.name)
    wb.save(export_path)
    return export_path


@router.message(F.text == 'Управление пулом')
@router.callback_query(F.data == 'menu:pool')
async def pool_menu(event: Message | CallbackQuery) -> None:
    msg = event.message if isinstance(event, CallbackQuery) else event
    await msg.answer('Управление пулом:', reply_markup=pool_menu_keyboard())
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.message(F.text == '/pool_import')
@router.callback_query(F.data == 'pool:import')
async def import_request(event: Message | CallbackQuery, state: FSMContext) -> None:
    msg = event.message if isinstance(event, CallbackQuery) else event
    await state.set_state(PoolStates.waiting_import_file)
    await msg.answer('Пришлите CRM xlsx для мягкого импорта товаров.', reply_markup=back_keyboard('menu:pool'))
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.message(PoolStates.waiting_import_file, F.document)
async def import_file(message: Message, state: FSMContext, session: AsyncSession) -> None:
    doc = message.document
    if not doc.file_name.lower().endswith('.xlsx'):
        await message.answer('Ожидается .xlsx файл.')
        return
    tmp = Path('tmp')
    tmp.mkdir(exist_ok=True)
    local = tmp / f'pool_{doc.file_unique_id}.xlsx'
    await message.bot.download(doc, destination=local)

    settings = get_settings()
    parser = CRMExcelParser(CRMParserConfig(settings.crm_name_column, settings.crm_stock_column, settings.crm_header_row))
    stock_map = parser.parse_stock(local)
    added, existed = await ProductService(session).import_pool(list(stock_map.keys()))
    await message.answer(f'Импорт завершен. Добавлено: {added}, уже существовало: {existed}.', reply_markup=pool_menu_keyboard())
    await state.clear()


@router.message(F.text == '/pool_add')
@router.callback_query(F.data == 'pool:add')
async def pool_add_start(event: Message | CallbackQuery, state: FSMContext) -> None:
    msg = event.message if isinstance(event, CallbackQuery) else event
    await state.set_state(PoolStates.waiting_manual_name)
    await msg.answer('Введите полное наименование:', reply_markup=back_keyboard('menu:pool'))
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.message(PoolStates.waiting_manual_name)
async def pool_add_name(message: Message, state: FSMContext) -> None:
    await state.update_data(full_name=message.text or '')
    await state.set_state(PoolStates.waiting_manual_aliases)
    await message.answer('Введите алиасы через запятую (или -):', reply_markup=back_keyboard('menu:pool'))


@router.message(PoolStates.waiting_manual_aliases)
async def pool_add_aliases(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    aliases = '' if (message.text or '').strip() == '-' else (message.text or '')
    product = await ProductService(session).add_manual(data['full_name'], aliases)
    await message.answer(f'Товар добавлен: {product.full_name} (id={product.id}).', reply_markup=pool_menu_keyboard())
    await state.clear()


@router.callback_query(F.data == 'pool:search')
async def pool_search_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PoolStates.waiting_search_query)
    await callback.message.answer('Введите строку поиска:', reply_markup=back_keyboard('menu:pool'))
    await callback.answer()


@router.message(PoolStates.waiting_search_query)
@router.message(F.text.startswith('/pool_search'))
async def pool_search(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if await state.get_state() == PoolStates.waiting_search_query.state:
        text = (message.text or '').strip()
    else:
        query = (message.text or '').split(maxsplit=1)
        if len(query) < 2:
            await message.answer('Использование: /pool_search <текст>')
            return
        text = query[1]
    products = await ProductService(session).search_active(text, limit=15)
    if not products:
        await message.answer('Ничего не найдено.', reply_markup=pool_menu_keyboard())
        await state.clear()
        return
    lines = [f"{p.id}: {p.full_name}" for p in products]
    await message.answer('\n'.join(lines), reply_markup=pool_menu_keyboard())
    await state.clear()


@router.callback_query(F.data == 'pool:archive')
async def pool_archive_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PoolStates.waiting_archive_id)
    await callback.message.answer('Введите ID товара для архивации:', reply_markup=back_keyboard('menu:pool'))
    await callback.answer()


@router.message(PoolStates.waiting_archive_id)
@router.message(F.text.startswith('/pool_archive'))
async def pool_archive(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if await state.get_state() == PoolStates.waiting_archive_id.state:
        raw_id = (message.text or '').strip()
    else:
        parts = (message.text or '').split()
        raw_id = parts[1] if len(parts) == 2 else ''
    if not raw_id.isdigit():
        await message.answer('Нужен корректный числовой id.')
        return
    ps = ProductService(session)
    product = await ps.get(int(raw_id))
    if not product:
        await message.answer('Товар не найден.')
        return
    await ps.archive(product, False)
    await message.answer('Товар архивирован.', reply_markup=pool_menu_keyboard())
    await state.clear()


@router.callback_query(F.data == 'pool:restore')
async def pool_restore_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PoolStates.waiting_restore_id)
    await callback.message.answer('Введите ID товара для восстановления:', reply_markup=back_keyboard('menu:pool'))
    await callback.answer()


@router.message(PoolStates.waiting_restore_id)
@router.message(F.text.startswith('/pool_restore'))
async def pool_restore(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if await state.get_state() == PoolStates.waiting_restore_id.state:
        raw_id = (message.text or '').strip()
    else:
        parts = (message.text or '').split()
        raw_id = parts[1] if len(parts) == 2 else ''
    if not raw_id.isdigit():
        await message.answer('Нужен корректный числовой id.')
        return
    ps = ProductService(session)
    product = await ps.get(int(raw_id))
    if not product:
        await message.answer('Товар не найден.')
        return
    await ps.archive(product, True)
    await message.answer('Товар восстановлен.', reply_markup=pool_menu_keyboard())
    await state.clear()


@router.callback_query(F.data == 'pool:rename')
async def pool_rename_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PoolStates.waiting_rename_id)
    await callback.message.answer('Введите ID товара для переименования:', reply_markup=back_keyboard('menu:pool'))
    await callback.answer()


@router.message(PoolStates.waiting_rename_id)
async def pool_rename_id(message: Message, state: FSMContext) -> None:
    raw = (message.text or '').strip()
    if not raw.isdigit():
        await message.answer('Нужен числовой id.')
        return
    await state.update_data(rename_id=int(raw))
    await state.set_state(PoolStates.waiting_rename_name)
    await message.answer('Введите новое наименование:', reply_markup=back_keyboard('menu:pool'))


@router.message(PoolStates.waiting_rename_name)
@router.message(F.text.startswith('/pool_rename'))
async def pool_rename(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if await state.get_state() == PoolStates.waiting_rename_name.state:
        data = await state.get_data()
        pid = data.get('rename_id')
        new_name = (message.text or '').strip()
    else:
        parts = (message.text or '').split(maxsplit=2)
        pid = int(parts[1]) if len(parts) == 3 and parts[1].isdigit() else None
        new_name = parts[2] if len(parts) == 3 else ''
    if not pid or not new_name:
        await message.answer('Нужны id и новое имя.')
        return
    ps = ProductService(session)
    product = await ps.get(pid)
    if not product:
        await message.answer('Товар не найден.')
        return
    await ps.update_name(product, new_name)
    await message.answer('Наименование обновлено.', reply_markup=pool_menu_keyboard())
    await state.clear()


@router.callback_query(F.data == 'pool:aliases')
async def pool_aliases_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PoolStates.waiting_aliases_id)
    await callback.message.answer('Введите ID товара для обновления алиасов:', reply_markup=back_keyboard('menu:pool'))
    await callback.answer()


@router.message(PoolStates.waiting_aliases_id)
async def pool_aliases_id(message: Message, state: FSMContext) -> None:
    raw = (message.text or '').strip()
    if not raw.isdigit():
        await message.answer('Нужен числовой id.')
        return
    await state.update_data(aliases_id=int(raw))
    await state.set_state(PoolStates.waiting_aliases_value)
    await message.answer('Введите алиасы через запятую:', reply_markup=back_keyboard('menu:pool'))


@router.message(PoolStates.waiting_aliases_value)
@router.message(F.text.startswith('/pool_aliases'))
async def pool_aliases(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if await state.get_state() == PoolStates.waiting_aliases_value.state:
        data = await state.get_data()
        pid = data.get('aliases_id')
        aliases = (message.text or '').strip()
    else:
        parts = (message.text or '').split(maxsplit=2)
        pid = int(parts[1]) if len(parts) == 3 and parts[1].isdigit() else None
        aliases = parts[2] if len(parts) == 3 else ''
    if not pid:
        await message.answer('Нужен id товара.')
        return
    ps = ProductService(session)
    product = await ps.get(pid)
    if not product:
        await message.answer('Товар не найден.')
        return
    await ps.update_aliases(product, aliases)
    await message.answer('Алиасы обновлены.', reply_markup=pool_menu_keyboard())
    await state.clear()


@router.callback_query(F.data == 'pool:export')
async def pool_export(callback: CallbackQuery, session: AsyncSession) -> None:
    products = await ProductService(session).list_for_export()
    if not products:
        await callback.message.answer('В базе нет товаров для выгрузки.', reply_markup=pool_menu_keyboard())
        await callback.answer()
        return

    export_path = _build_pool_export(products)
    try:
        await callback.message.answer_document(
            document=FSInputFile(export_path),
            caption=f'Выгрузка базы товаров ({len(products)} шт.)',
            reply_markup=pool_menu_keyboard(),
        )
    finally:
        export_path.unlink(missing_ok=True)
    await callback.answer()
