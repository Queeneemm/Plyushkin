import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.handlers import access, history, inventory, pool, start, summary
from bot.middlewares.auth import AccessMiddleware
from bot.middlewares.db import DbSessionMiddleware
from config.settings import get_settings
from db.init_db import init_db


async def main() -> None:
    settings = get_settings()
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

    await init_db()

    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.message.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(DbSessionMiddleware())
    dp.message.middleware(AccessMiddleware())
    dp.callback_query.middleware(AccessMiddleware())

    dp.include_routers(start.router, inventory.router, pool.router, access.router, history.router, summary.router)

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
