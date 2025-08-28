from sqlalchemy import String, BigInteger, Integer, Date, Time, ForeignKey, Enum, Text, Float, Boolean, text, DateTime, \
    CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, engine
import enum
from datetime import datetime



class Supplier(Base):
    __tablename__ = 'suppliers'

    id_supplier: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    platform: Mapped[str] = mapped_column(String, nullable=False)
    contact_info: Mapped[str] = mapped_column(Text)
    min_order_value: Mapped[float] = mapped_column(Float, nullable=False)
    shipping_method: Mapped[str] = mapped_column(Text, nullable=True)
    avg_delivery_days: Mapped[int] = mapped_column(Integer, nullable=True)
    active: Mapped[Boolean] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("datetime('now', 'localtime')"))
    __table_args__ = (CheckConstraint('active IN (0, 1)'),)


class Product(Base):
    __tablename__ ='products'


    id_product: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    price_rub: Mapped[float] = mapped_column(Float, nullable=False)
    original_price_yuan: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String, default='обувь', index=True)
    taobao_url: Mapped[str] = mapped_column(String, nullable=False)
    taobao_item_id: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    image_urls: Mapped[str] = mapped_column(Text, nullable=True)
    attributes: Mapped[str] = mapped_column(Text, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("datetime('now', 'localtime')"),
                          server_onupdate=text("datetime('now', 'localtime')"))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("datetime('now', 'localtime')"))
    __table_args__ = (CheckConstraint('price_rub > 0'),)

    cart_items: Mapped[list["Cart"]] = relationship("Cart", back_populates="product")
    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="product")


class User(Base):
    __tablename__ = 'users'

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String, nullable=True)
    last_name: Mapped[str] = mapped_column(String, nullable=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    username: Mapped[str] = mapped_column(String, nullable=True)
    phone: Mapped[str] = mapped_column(String, nullable=True)
    delivery_address: Mapped[str] = mapped_column(Text, nullable=True)
    city: Mapped[str] = mapped_column(String, nullable=True)
    country: Mapped[str] = mapped_column(String, nullable=False, default='Russia')
    language: Mapped[str] = mapped_column(String, nullable=False, default='ru')
    email: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("datetime('now', 'localtime')"))
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("datetime('now', 'localtime')"),
                        server_onupdate=text("datetime('now', 'localtime')"))

    sessions: Mapped[list["UserSession"]] = relationship("UserSession", back_populates="customer", cascade="all, delete-orphan")
    cart_items: Mapped[list["Cart"]] = relationship("Cart", back_populates="customer", cascade="all, delete-orphan")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="customer", cascade="all, delete-orphan")


class UserSession(Base):
    __tablename__ = 'user_sessions'

    id_session: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_customer: Mapped[int] = mapped_column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    results_json: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default='active')
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("datetime('now', 'localtime')"))
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("datetime('now', '+1 hour')"), index=True)
    __table_args__=  (CheckConstraint("status IN ('active', 'completed', 'expired')"),)

    customer: Mapped[User] = relationship("User", back_populates="sessions")


class Cart(Base):
    __tablename__ = 'cart'

    id_cart: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_customer: Mapped[int] = mapped_column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    # В оригинальной схеме id_product был NOT NULL, что конфликтует с ON DELETE SET NULL.
    # Устанавливаем nullable=True, чтобы ON DELETE SET NULL работал корректно.
    id_product: Mapped[int] = mapped_column(Integer, ForeignKey('products.id_product', ondelete='SET NULL'), nullable=True)
    size: Mapped[str] = mapped_column(String, nullable=True)
    color: Mapped[str] = mapped_column(String, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    added_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("datetime('now', 'localtime')"))
    __table_args__ = (
        UniqueConstraint('id_customer', 'id_product', 'size', 'color', name='uq_cart_item'),
        CheckConstraint('quantity >= 1 AND quantity <= 10'),
    )

    customer: Mapped["User"] = relationship("User", back_populates="cart_items")
    product: Mapped["Product"] = relationship("Product", back_populates="cart_items")


class Order(Base):
    __tablename__ = 'orders'
    id_order: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_customer: Mapped[int] = mapped_column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    total_amount_rub: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False, default='RUB')
    order_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("datetime('now', 'localtime')"), index=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default='pending', index=True)
    payment_status: Mapped[str] = mapped_column(String, nullable=False, default='unpaid', index=True)
    payment_method: Mapped[str]
    delivery_address: Mapped[text] = mapped_column(Text, nullable=False)
    tracking_number: Mapped[str]
    admin_note: Mapped[str] = mapped_column(Text, nullable=True)
    exchange_rate_used: Mapped[float] = mapped_column(Float, nullable=False)
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'confirmed', 'paid', 'processing_supplier', 'shipped', 'delivered', 'cancelled')"),
        CheckConstraint("payment_status IN ('unpaid', 'paid', 'refunded')"),
    )

    customer: Mapped["User"] = relationship("User", back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = 'order_items'

    id_item: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_order: Mapped[int] = mapped_column(Integer, ForeignKey('orders.id_order', ondelete='CASCADE'), nullable=False, index=True)
    id_product: Mapped[int] = mapped_column(Integer, ForeignKey('products.id_product', ondelete='SET NULL'), nullable=True)
    product_name: Mapped[str] = mapped_column(String, nullable=False)
    product_price_rub: Mapped[float] = mapped_column(Float, nullable=False)
    size: Mapped[str] = mapped_column(String, nullable=True)
    color: Mapped[str] = mapped_column(String, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)

    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped["Product"] = relationship("Product", back_populates="order_items")


class ExchangeRate(Base):
    __tablename__ = 'exchange_rates'

    id_rate: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rate_rub: Mapped[Float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String, default='manual')
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("datetime('now', 'localtime')"), index=True)


class Analytics(Base):
    __tablename__ = 'analytics'

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, primary_key=True, server_default=text("datetime('now', 'localtime')"))


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)



# Таблица пользователей
'''class User(Base):
    __tablename__ = 'users'

    telegram_id: Mapped[int] = mapped_column(BigInteger,
                                             primary_key=True)  # Уникальный идентификатор пользователя в Telegram
    first_name: Mapped[str] = mapped_column(String, nullable=False)  # Имя пользователя
    username: Mapped[str] = mapped_column(String, nullable=True)  # Telegram username

    # Связь с заявками (один пользователь может иметь несколько заявок)
    applications: Mapped[list["Application"]] = relationship(back_populates="user")




class Application(Base):
    __tablename__ = 'applications'

    class GenderEnum(enum.Enum):
        male = "Мужской"
        female = "Женский"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # Уникальный идентификатор заявки
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.telegram_id'))  # Внешний ключ на пользователя
    appointment_date: Mapped[Date] = mapped_column(Date, nullable=False)  # Дата заявки
    appointment_time: Mapped[Time] = mapped_column(Time, nullable=False)  # Время заявки
    gender: Mapped[GenderEnum] = mapped_column(Enum(GenderEnum), nullable=False)
    client_name: Mapped[str] = mapped_column(String, nullable=False)  # Имя пользователя

    user: Mapped["User"] = relationship(back_populates="applications")'''