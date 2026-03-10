from db.base import Base
from db.models import User, AllowedChat, Product, ProductAlias, InventorySession, InventoryItem
from db.session import engine


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
