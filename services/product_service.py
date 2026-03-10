from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.utils.text import normalize_name, parse_aliases
from db.models import Product, ProductAlias, ProductCreatedFrom


class ProductService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def search_active(self, query: str, limit: int = 12) -> list[Product]:
        q = f"%{query.lower()}%"
        stmt = (
            select(Product)
            .options(selectinload(Product.aliases))
            .where(
                Product.is_active.is_(True),
                or_(
                    func.lower(Product.full_name).like(q),
                    Product.id.in_(
                        select(ProductAlias.product_id).where(func.lower(ProductAlias.alias).like(q))
                    ),
                ),
            )
            .order_by(Product.full_name)
            .limit(limit)
        )
        return list((await self.session.scalars(stmt)).all())

    async def get(self, product_id: int) -> Product | None:
        return await self.session.scalar(select(Product).options(selectinload(Product.aliases)).where(Product.id == product_id))

    async def add_manual(self, full_name: str, aliases_raw: str) -> Product:
        product = Product(full_name=normalize_name(full_name), created_from=ProductCreatedFrom.manual)
        self.session.add(product)
        await self.session.flush()
        for alias in parse_aliases(aliases_raw):
            self.session.add(ProductAlias(product_id=product.id, alias=alias))
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def update_name(self, product: Product, full_name: str) -> None:
        product.full_name = normalize_name(full_name)
        await self.session.commit()

    async def update_aliases(self, product: Product, aliases_raw: str) -> None:
        await self.session.execute(ProductAlias.__table__.delete().where(ProductAlias.product_id == product.id))
        for alias in parse_aliases(aliases_raw):
            self.session.add(ProductAlias(product_id=product.id, alias=alias))
        await self.session.commit()

    async def archive(self, product: Product, active: bool) -> None:
        product.is_active = active
        await self.session.commit()

    async def list_all(self, include_archived: bool = False, limit: int = 30) -> list[Product]:
        stmt = select(Product).order_by(Product.full_name).limit(limit)
        if not include_archived:
            stmt = stmt.where(Product.is_active.is_(True))
        return list((await self.session.scalars(stmt)).all())

    async def import_pool(self, names: list[str]) -> tuple[int, int]:
        added = 0
        existed = 0
        for raw in names:
            full_name = normalize_name(raw)
            if not full_name:
                continue
            found = await self.session.scalar(select(Product).where(func.lower(Product.full_name) == full_name.lower()))
            if found:
                existed += 1
                continue
            self.session.add(Product(full_name=full_name, created_from=ProductCreatedFrom.crm, is_active=True))
            added += 1
        await self.session.commit()
        return added, existed
