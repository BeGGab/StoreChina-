import logging

from sqlalchemy import event
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete, func

from app.database import Base, engine, async_session_maker
from app.api.models import User, Order, OrderItem, ExchangeRate


logger = logging.getLogger(__name__)


class BaseDAO:
    model = None  # Устанавливается в дочернем классе

    @classmethod
    async def find_one_or_none_by_id(cls, data_id: int):
        # Найти запись по ID
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(id=data_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def find_one_or_none(cls, **filter_by):
        # Найти одну запись по фильтрам
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def find_all(cls, **filter_by):
        # Найти все записи по фильтрам
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def add(cls, **values):
        # Добавить одну запись
        async with async_session_maker() as session:
            async with session.begin():
                new_instance = cls.model(**values)
                session.add(new_instance)
                try:
                    await session.commit()
                except SQLAlchemyError as e:
                    await session.rollback()
                    raise e
                return new_instance

    @classmethod
    async def add_many(cls, instances: list[dict]):
        # Добавить несколько записей
        async with async_session_maker() as session:
            async with session.begin():
                new_instances = [cls.model(**values) for values in instances]
                session.add_all(new_instances)
                try:
                    await session.commit()
                except SQLAlchemyError as e:
                    await session.rollback()
                    raise e
                return new_instances

    @classmethod
    async def update(cls, filter_by, **values):
        # Обновить записи по фильтру
        async with async_session_maker() as session:
            async with session.begin():
                query = (
                    sqlalchemy_update(cls.model)
                    .where(*[getattr(cls.model, k) == v for k, v in filter_by.items()])
                    .values(**values)
                    .execution_options(synchronize_session="fetch")
                )
                result = await session.execute(query)
                try:
                    await session.commit()
                except SQLAlchemyError as e:
                    await session.rollback()
                    raise e
                return result.rowcount

    @classmethod
    async def delete(cls, delete_all: bool = False, **filter_by):
        # Удалить записи по фильтру
        if not delete_all and not filter_by:
            raise ValueError("Нужен хотя бы один фильтр для удаления.")

        async with async_session_maker() as session:
            async with session.begin():
                query = sqlalchemy_delete(cls.model).filter_by(**filter_by)
                result = await session.execute(query)
                try:
                    await session.commit()
                except SQLAlchemyError as e:
                    await session.rollback()
                    raise e
                return result.rowcount

    @classmethod
    async def count(cls, **filter_by):
        # Подсчитать количество записей
        async with async_session_maker() as session:
            query = select(func.count(cls.model.id)).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalar()

    @classmethod
    async def exists(cls, **filter_by):
        # Проверить существование записи
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by).exists()
            result = await session.execute(query)
            return result.scalar()

    @classmethod
    async def paginate(cls, page: int = 1, page_size: int = 10, **filter_by):
        # Пагинация записей
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query.offset((page - 1) * page_size).limit(page_size))
            return result.scalars().all()
        

async def init_db():
    """Создаёт базу данных и все таблицы, если их нет, используя SQLAlchemy."""
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with async_session_maker() as session:
            async with session.begin():
                query = select(func.count(ExchangeRate.id_rate))
                count = (await session.execute(query)).scalar()
                if count == 0:
                    initial_rate = ExchangeRate(rate_rub=12.5, source='manual')
                    session.add(initial_rate)
        logger.info("База данных инициализирована с использованием SQLAlchemy")
    except Exception as e:
        logger.error("Ошибка инициализации БД с SQLAlchemy: %s", e)


