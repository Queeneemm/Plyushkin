from pathlib import Path

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states.forms import PoolStates
from config.settings import get_settings
from services.crm_parser import CRMExcelParser, CRMParserConfig
from services.product_service import ProductService

router = Router()


@router.message(F.text == 'Управление пулом')
async def pool_menu(message: Message) -> None:
    await message.answer(
        'Команды пула:\n'
        '/pool_import - импорт из CRM xlsx\n'
        '/pool_add - добавить вручную\n'
        '/pool_search <текст> - поиск\n'
        '/pool_archive <id> - архивировать\n'
        '/pool_restore <id> - восстановить\n'
        '/pool_rename <id> <новое имя> - переименовать\n'
        '/pool_aliases <id> <alias1,alias2> - алиасы'
    )


@router.message(F.text == '/pool_import')
async def import_request(message: Message, state: FSMContext) -> None:
    await state.set_state(PoolStates.waiting_import_file)
    await message.answer('Пришлите CRM xlsx для мягкого импорта товаров.')


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
    await message.answer(f'Импорт завершен. Добавлено: {added}, уже существовало: {existed}.')
    await state.clear()


@router.message(F.text == '/pool_add')
async def pool_add_start(message: Message, state: FSMContext) -> None:
    await state.set_state(PoolStates.waiting_manual_name)
    await message.answer('Введите полное наименование:')


@router.message(PoolStates.waiting_manual_name)
async def pool_add_name(message: Message, state: FSMContext) -> None:
    await state.update_data(full_name=message.text or '')
    await state.set_state(PoolStates.waiting_manual_aliases)
    await message.answer('Введите алиасы через запятую (или -):')


@router.message(PoolStates.waiting_manual_aliases)
async def pool_add_aliases(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    aliases = '' if (message.text or '').strip() == '-' else (message.text or '')
    product = await ProductService(session).add_manual(data['full_name'], aliases)
    await message.answer(f'Товар добавлен: {product.full_name} (id={product.id}).')
    await state.clear()


@router.message(F.text.startswith('/pool_search'))
async def pool_search(message: Message, session: AsyncSession) -> None:
    query = (message.text or '').split(maxsplit=1)
    if len(query) < 2:
        await message.answer('Использование: /pool_search <текст>')
        return
    products = await ProductService(session).search_active(query[1], limit=15)
    if not products:
        await message.answer('Ничего не найдено.')
        return
    lines = [f"{p.id}: {p.full_name}" for p in products]
    await message.answer('\n'.join(lines))


@router.message(F.text.startswith('/pool_archive'))
async def pool_archive(message: Message, session: AsyncSession) -> None:
    parts = (message.text or '').split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer('Использование: /pool_archive <id>')
        return
    ps = ProductService(session)
    product = await ps.get(int(parts[1]))
    if not product:
        await message.answer('Товар не найден.')
        return
    await ps.archive(product, False)
    await message.answer('Товар архивирован.')


@router.message(F.text.startswith('/pool_restore'))
async def pool_restore(message: Message, session: AsyncSession) -> None:
    parts = (message.text or '').split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer('Использование: /pool_restore <id>')
        return
    ps = ProductService(session)
    product = await ps.get(int(parts[1]))
    if not product:
        await message.answer('Товар не найден.')
        return
    await ps.archive(product, True)
    await message.answer('Товар восстановлен.')


@router.message(F.text.startswith('/pool_rename'))
async def pool_rename(message: Message, session: AsyncSession) -> None:
    parts = (message.text or '').split(maxsplit=2)
    if len(parts) != 3 or not parts[1].isdigit():
        await message.answer('Использование: /pool_rename <id> <новое имя>')
        return
    ps = ProductService(session)
    product = await ps.get(int(parts[1]))
    if not product:
        await message.answer('Товар не найден.')
        return
    await ps.update_name(product, parts[2])
    await message.answer('Наименование обновлено.')


@router.message(F.text.startswith('/pool_aliases'))
async def pool_aliases(message: Message, session: AsyncSession) -> None:
    parts = (message.text or '').split(maxsplit=2)
    if len(parts) != 3 or not parts[1].isdigit():
        await message.answer('Использование: /pool_aliases <id> <alias1,alias2>')
        return
    ps = ProductService(session)
    product = await ps.get(int(parts[1]))
    if not product:
        await message.answer('Товар не найден.')
        return
    await ps.update_aliases(product, parts[2])
    await message.answer('Алиасы обновлены.')
