import logging
from sqlalchemy import event
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from app.dao.base import BaseDAO
from app.api.models import User, Order, OrderItem, ExchangeRate
from app.database import async_session_maker


logger = logging.getLogger(__name__)



class UserDAO(BaseDAO):
    model = User

    @classmethod
    async def register_or_update(cls, telegram_id: int, **data):
        """Регистрирует или обновляет клиента."""
        async with async_session_maker() as session:
            try:
                # Начинаем транзакцию
                async with session.begin():
                    # 1. Ищем пользователя
                    query = select(cls.model).filter_by(telegram_id=telegram_id)
                    result = await session.execute(query)
                    user = result.scalar_one_or_none()

                    # 2. Готовим данные
                    first_name = data.get('first_name') or "Клиент"
                    last_name = data.get('last_name') or " "
                    full_name = f"{first_name} {last_name}".strip()

                    if user:
                        # 3a. Обновляем существующего пользователя
                        user.full_name = full_name
                        user.username = data.get('username')
                        user.phone = data.get('phone')
                        user.delivery_address = data.get('address')
                        user.city = data.get('city')
                        user.email = data.get('email')
                        user.updated_at = func.now()
                        logger.info("Клиент %s обновлён", telegram_id)
                    else:
                        # 3b. Создаём нового пользователя с правильными аргументами
                        user = cls.model(
                            telegram_id=telegram_id,
                            full_name=full_name,
                            username=data.get('username'),
                            phone=data.get('phone'),
                            delivery_address=data.get('address'),
                            city=data.get('city'),
                            email=data.get('email'),
                        )
                        session.add(user)
                        logger.info("Клиент %s зарегистрирован", telegram_id)

                # После коммита возвращаем объект пользователя
                return await session.get(cls.model, user.user_id)
            except SQLAlchemyError as e:
                logger.error("Ошибка регистрации клиента %s: %s", telegram_id, e)
                return None


class OrderDAO(BaseDAO):
    model = Order

    @classmethod
    async def save_order_with_items(cls, user_info: dict, order_data: dict):
        """Сохраняет заказ и позиции в БД."""
        async with async_session_maker() as session:
            try:
                async with session.begin():
                    user_id = user_info.get('id')
                    if not user_id:
                        logger.error("Нет user_id в user_info")
                        return None

                    customer = await session.scalar(select(User).filter_by(telegram_id=user_id))
                    if not customer:
                        customer = await UserDAO.register_or_update(
                            telegram_id=user_id,
                            first_name=user_info.get('first_name') or user_info.get('name', 'Клиент'),
                            last_name=user_info.get('last_name'),
                            username=user_info.get('username'),
                            phone=user_info.get('phone'),
                            address=user_info.get('address'),
                            city=user_info.get('city'),
                            email=user_info.get('email')
                        )
                        if not customer:
                            logger.error("Не удалось создать или найти клиента %s", user_id)
                            return None

                    rate_query = select(ExchangeRate.rate_rub).order_by(ExchangeRate.recorded_at.desc()).limit(1)
                    exchange_rate = (await session.execute(rate_query)).scalar_one_or_none() or 12.5

                    new_order = Order(
                        id_customer=customer.user_id,
                        total_amount_rub=round(order_data['total'], 2),
                        delivery_address=user_info.get('address', 'Не указан'),
                        order_date=order_data['timestamp'],
                        exchange_rate_used=exchange_rate
                    )
                    session.add(new_order)
                    await session.flush()
                    order_id = new_order.id_order

                    items_to_add = [OrderItem(
                        id_order=order_id, id_product=item.get('id_product'),
                        product_name=item['name'], product_price_rub=item['price'],
                        size=item.get('size'), color=item.get('color'),
                        quantity=item.get('quantity', 1),
                        subtotal=item['price'] * item.get('quantity', 1)
                    ) for item in order_data['items']]
                    session.add_all(items_to_add)

                logger.info("Заказ #%s сохранён для пользователя %s", order_id, user_id)
                return order_id
            except SQLAlchemyError as e:
                logger.error("Ошибка сохранения заказа: %s", e)
                return None

    @classmethod
    async def get_recent(cls, limit: int = 10):
        """Возвращает последние заказы с именами клиентов и адресами из заказа."""
        limit = max(1, min(limit, 100))
        async with async_session_maker() as session:
            try:
                query = (
                    select(
                        cls.model.id_order, cls.model.total_amount_rub, cls.model.order_date,
                        cls.model.status, User.full_name, User.phone,
                        cls.model.delivery_address
                    )
                    .join(User, cls.model.id_customer == User.user_id)
                    .order_by(cls.model.order_date.desc()).limit(limit)
                )
                result = await session.execute(query)
                return result.mappings().all()
            except SQLAlchemyError as e:
                logger.error("Ошибка получения заказов: %s", e)
                return []


class StatsDAO:
    @classmethod
    async def get_stats(cls):
        """Возвращает статистику: количество клиентов и заказов."""
        async with async_session_maker() as session:
            try:
                users_query = select(func.count(User.user_id))
                users = (await session.execute(users_query)).scalar_one()
                orders_query = select(func.count(Order.id_order))
                orders = (await session.execute(orders_query)).scalar_one()
                return {"users": users, "orders": orders}
            except SQLAlchemyError as e:
                logger.error("Ошибка получения статистики: %s", e)
                return {"users": 0, "orders": 0}

'''class ApplicationDAO(BaseDAO):
    model = Application

    @classmethod
    async def get_applications_by_user(cls, user_id: int):
        """
        Возвращает все заявки пользователя по user_id с дополнительной информацией
        о мастере и услуге.

        Аргументы:
            user_id: Идентификатор пользователя.

        Возвращает:
            Список заявок пользователя с именами мастеров и услуг.
        """
        async with async_session_maker() as session:
            try:
                # Используем joinedload для ленивой загрузки связанных объектов
                query = (
                    select(cls.model)
                    .options(joinedload(cls.model.master), joinedload(cls.model.service))
                    .filter_by(user_id=user_id)
                )
                result = await session.execute(query)
                applications = result.scalars().all()

                # Возвращаем список словарей с нужными полями
                return [
                    {
                        "application_id": app.id,
                        "service_name": app.service.service_name,  # Название услуги
                        "master_name": app.master.master_name,  # Имя мастера
                        "appointment_date": app.appointment_date,
                        "appointment_time": app.appointment_time,
                        "gender": app.gender.value,
                    }
                    for app in applications
                ]
            except SQLAlchemyError as e:
                print(f"Error while fetching applications for user {user_id}: {e}")
                return None

    @classmethod
    async def get_all_applications(cls):
        """
        Возвращает все заявки в базе данных с дополнительной информацией о мастере и услуге.

        Возвращает:
            Список всех заявок с именами мастеров и услуг.
        """
        async with async_session_maker() as session:
            try:
                # Используем joinedload для загрузки связанных данных
                query = (
                    select(cls.model)
                    .options(joinedload(cls.model.master), joinedload(cls.model.service))
                )
                result = await session.execute(query)
                applications = result.scalars().all()

                # Возвращаем список словарей с нужными полями
                return [
                    {
                        "application_id": app.id,
                        "user_id": app.user_id,
                        "service_name": app.service.service_name,  # Название услуги
                        "master_name": app.master.master_name,  # Имя мастера
                        "appointment_date": app.appointment_date,
                        "appointment_time": app.appointment_time,
                        "client_name": app.client_name,  # Имя клиента
                        "gender": app.gender.value  # Пол клиента
                    }
                    for app in applications
                ]
            except SQLAlchemyError as e:
                print(f"Error while fetching all applications: {e}")
                return None'''
