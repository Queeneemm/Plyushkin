from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import InventoryItem, InventorySession, Product, SessionStatus


class InventoryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_session(self) -> InventorySession | None:
        return await self.session.scalar(select(InventorySession).where(InventorySession.status == SessionStatus.active))

    async def get_or_create_active(self, user_id: int) -> InventorySession:
        active = await self.get_active_session()
        if active:
            return active
        s = InventorySession(status=SessionStatus.active, created_by_user_id=user_id)
        self.session.add(s)
        await self.session.commit()
        await self.session.refresh(s)
        return s

    async def get_item(self, session_id: int, product_id: int) -> InventoryItem | None:
        return await self.session.scalar(
            select(InventoryItem).where(InventoryItem.session_id == session_id, InventoryItem.product_id == product_id)
        )

    async def upsert_item(self, session_id: int, product_id: int, qty: float, mode: str = 'replace') -> InventoryItem:
        item = await self.get_item(session_id, product_id)
        qty_dec = Decimal(str(qty))
        if item:
            if mode == 'add':
                item.quantity_fact = Decimal(item.quantity_fact) + qty_dec
            else:
                item.quantity_fact = qty_dec
            item.updated_at = datetime.utcnow()
        else:
            item = InventoryItem(session_id=session_id, product_id=product_id, quantity_fact=qty_dec)
            self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def list_items(self, session_id: int) -> list[InventoryItem]:
        stmt = (
            select(InventoryItem)
            .options(selectinload(InventoryItem.product))
            .where(InventoryItem.session_id == session_id)
            .order_by(InventoryItem.updated_at.desc())
        )
        return list((await self.session.scalars(stmt)).all())

    async def delete_item(self, item_id: int) -> None:
        item = await self.session.get(InventoryItem, item_id)
        if item:
            await self.session.delete(item)
            await self.session.commit()

    async def finish_session(self, session_id: int, url: str | None, tab_name: str | None) -> None:
        s = await self.session.get(InventorySession, session_id)
        if not s:
            return
        s.status = SessionStatus.finished
        s.finished_at = datetime.utcnow()
        s.google_sheet_url = url
        s.google_sheet_tab_name = tab_name
        await self.session.commit()

    async def cancel_active_session(self) -> InventorySession | None:
        s = await self.get_active_session()
        if not s:
            return None
        s.status = SessionStatus.cancelled
        s.finished_at = datetime.utcnow()
        await self.session.commit()
        return s

    async def history(self, limit: int = 20) -> list[InventorySession]:
        return list((await self.session.scalars(select(InventorySession).where(InventorySession.status == SessionStatus.finished).order_by(InventorySession.finished_at.desc()).limit(limit))).all())

    async def session_card(self, session_id: int) -> dict:
        session = await self.session.get(InventorySession, session_id)
        count = await self.session.scalar(select(func.count(InventoryItem.id)).where(InventoryItem.session_id == session_id))
        return {'session': session, 'items_count': count or 0}

    async def delete_session(self, session_id: int) -> bool:
        session = await self.session.get(InventorySession, session_id)
        if not session:
            return False
        await self.session.delete(session)
        await self.session.commit()
        return True

    async def fact_map(self, session_id: int) -> dict[int, float]:
        items = await self.list_items(session_id)
        return {i.product_id: float(i.quantity_fact) for i in items}

    async def products_by_ids(self, ids: list[int]) -> dict[int, Product]:
        if not ids:
            return {}
        products = list((await self.session.scalars(select(Product).where(Product.id.in_(ids)))).all())
        return {p.id: p for p in products}
