from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class UserRole(str, Enum):
    admin = 'admin'
    user = 'user'


class SessionStatus(str, Enum):
    active = 'active'
    finished = 'finished'
    cancelled = 'cancelled'


class ProductCreatedFrom(str, Enum):
    crm = 'crm'
    manual = 'manual'


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.user)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AllowedChat(Base):
    __tablename__ = 'allowed_chats'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Product(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    created_from: Mapped[ProductCreatedFrom] = mapped_column(SAEnum(ProductCreatedFrom), default=ProductCreatedFrom.crm)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    aliases: Mapped[list[ProductAlias]] = relationship(back_populates='product', cascade='all,delete-orphan')


class ProductAlias(Base):
    __tablename__ = 'product_aliases'
    __table_args__ = (UniqueConstraint('product_id', 'alias', name='uq_product_alias'),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id', ondelete='CASCADE'))
    alias: Mapped[str] = mapped_column(String(255), index=True)

    product: Mapped[Product] = relationship(back_populates='aliases')


class InventorySession(Base):
    __tablename__ = 'inventory_sessions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[SessionStatus] = mapped_column(SAEnum(SessionStatus), default=SessionStatus.active, index=True)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    google_sheet_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    google_sheet_tab_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    items: Mapped[list[InventoryItem]] = relationship(back_populates='session', cascade='all,delete-orphan')


class InventoryItem(Base):
    __tablename__ = 'inventory_items'
    __table_args__ = (UniqueConstraint('session_id', 'product_id', name='uq_session_product'),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey('inventory_sessions.id', ondelete='CASCADE'), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'), index=True)
    quantity_fact: Mapped[float] = mapped_column(Numeric(12, 3), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    session: Mapped[InventorySession] = relationship(back_populates='items')
    product: Mapped[Product] = relationship()
