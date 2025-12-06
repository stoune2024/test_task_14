# app/repository.py

"""
Слой доступа к данным для службы ведущего маршрутизатора.
Использует SQLAlchemy AsyncSession для операций с базой данных.
"""

from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker
from app.models import (
    OperatorOut,
    SourceOut,
    OperatorSourceWeightCreate,
    ContactOut,
    OperatorUpdate,
    ContactCreate,
    LeadsAndContactsOut,
)
from app.schemas import Operator, Lead, Source, OperatorSourceWeight, Base, Contact
from settings import settings
from app.services import RoutingService
from sqlalchemy import create_engine


engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
sync_engine = create_engine(
    settings.DATABASE_URL.replace("+aiosqlite", ""), echo=False, future=True
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
SyncSessionLocal = sessionmaker(
    bind=sync_engine, autocommit=False, autoflush=False, class_=Session
)


async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


def get_session_sync() -> Session:
    session = SyncSessionLocal()
    try:
        yield session
    finally:
        session.close()


class OperatorRepository:
    """
    Класс для взаимодействия с сущностью Operator
    """

    @staticmethod
    async def create(
        db_session, name: str, is_active: bool, max_concurrent: int
    ) -> OperatorOut:
        """
        Функция создания оператора
        :param db_session: сессия БД
        :param name: имя оператора
        :param is_active: активен ли оператор
        :param max_concurrent: максимальная нагрузка оператора
        :return: модель OperatorOut
        """
        operator = Operator(
            name=name, is_active=is_active, max_concurrent=max_concurrent
        )
        db_session.add(operator)
        await db_session.commit()
        operator_out = OperatorOut(
            id=operator.id,
            name=name,
            is_active=is_active,
            max_concurrent=max_concurrent,
        )

        await db_session.refresh(operator)
        return operator_out

    @staticmethod
    async def get_all(db_session) -> List[OperatorOut]:
        """
        Функция возврата всех операторов
        :param db_session: сессия БД
        :return: список моделей OperatorOut
        """
        result = await db_session.execute(select(Operator))
        list_of_operators = []
        for o in result.scalars().all():
            operator_out = OperatorOut(
                id=o.id,
                name=o.name,
                is_active=o.is_active,
                max_concurrent=o.max_concurrent,
            )
            list_of_operators.append(operator_out)
        return list_of_operators

    @staticmethod
    async def update(
        db_session: AsyncSession,
        data: OperatorUpdate,
        operator_id: Optional[int] = None,
    ) -> OperatorOut:
        """
        Функция обновления конкретного оператора
        :param operator_id: идентификатор оператора
        :param db_session: сессия БД
        :param data: данные для обновления
        :return: модель OperatorOut
        """
        db_operator = await db_session.get(Operator, operator_id)

        if data.max_concurrent is not None:
            db_operator.max_concurrent = data.max_concurrent
        if data.is_active is not None:
            db_operator.is_active = data.is_active
        if data.name is not None:
            db_operator.name = data.name
        db_session.add(db_operator)
        await db_session.commit()

        operator_out = OperatorOut(
            id=db_operator.id,
            name=db_operator.name,
            is_active=db_operator.is_active,
            max_concurrent=db_operator.max_concurrent,
        )

        await db_session.refresh(db_operator)
        return operator_out


class LeadRepository:
    """
    Класс для взаимодействия с сущностью Lead
    """

    @staticmethod
    async def get_leads_and_contacts(db_session) -> List[LeadsAndContactsOut]:
        stmt = select(
            Lead.phone.label("leads_phone"),
            Lead.id.label("leads_id"),
            Contact.id.label("contacts_id"),
        ).join(Contact, Lead.id == Contact.lead_id)
        list_of_models = []
        result = await db_session.execute(stmt)
        rows = result.all()
        for row in rows:
            leads_and_models_model = LeadsAndContactsOut(
                lead_phone=row[0], lead_id=row[1], contact_id=row[2]
            )
            list_of_models.append(leads_and_models_model)
        return list_of_models


class SourceRepository:
    """
    Класс для взаимодействия с сущностью Source
    """

    @staticmethod
    async def create(session_db, name: str, code: str, description: str) -> SourceOut:
        """
        Функция создания источника
        :param description: описание источника
        :param session_db: сессия БД
        :param name: названия источника
        :param code: уникальный идентификатор источника
        :return: модель SourceOut
        """
        source = Source(name=name, code=code, description=description)
        session_db.add(source)
        await session_db.commit()
        source_out = SourceOut(
            id=source.id,
            code=source.code,
            name=source.name,
            description=source.description,
        )
        await session_db.refresh(source)
        return source_out


class WeightRepository:
    """
    Класс для взаимодействия с сущностью Weight
    """

    @staticmethod
    async def set_weights(
        db_session: AsyncSession,
        source_id: int,
        weights: List[OperatorSourceWeightCreate],
    ):
        """
        Функция установки весов операторов по конкретному источнику по его source_id
        :param db_session: сессия БД
        :param source_id: идентификатор источника
        :param weights: список моделей OperatorSourceWeightCreate
        :return: None
        """
        # Удаляем старые веса для источника source_id
        result = await db_session.execute(
            select(OperatorSourceWeight).where(
                OperatorSourceWeight.source_id == source_id
            )
        )
        for w in result.scalars().all():
            await db_session.delete(w)

        # Добавляем новые веса для источника source_id
        for w in weights:
            db_session.add(
                OperatorSourceWeight(
                    source_id=source_id,
                    operator_id=w.operator_id,
                    weight=w.weight,
                )
            )

        await db_session.commit()


class ContactRepository:
    """
    Класс для взаимодействия с сущностью Contact
    """

    @staticmethod
    async def create(
        data: ContactCreate,
        db_session,
        source_code: str,
    ) -> ContactOut:
        """
        Функция создания контакта
        :param source_code: уникальный строковый идентификатор источника
        :param db_session: синхронная сессия БД
        :param data: данные об обращении
        :return: модель ContactOut
        """
        contact = RoutingService.route_and_create_contact(
            db_session,
            external_id=data.external_id,
            phone=data.phone,
            email=data.email,
            source_code=source_code,
            payload=data.payload,
        )

        contact_out = ContactOut(
            id=contact.id,
            lead_id=contact.lead_id,
            source_id=contact.source_id,
            operator_id=contact.operator_id,
            status=contact.status,
            payload=contact.payload,
            created=contact.created_at,
        )
        return contact_out

    @staticmethod
    async def get_operator_stats(db_session):
        stmt = select(
            func.count(Contact.id).label("contacts_count"),
            Contact.operator_id.label("operator_id"),
        ).group_by(Contact.operator_id)
        result = await db_session.execute(stmt)
        rows = result.mappings().all()
        return rows

    @staticmethod
    async def get_source_stats(db_session):
        stmt = select(
            func.count(Contact.id).label("contacts_count"),
            Contact.source_id.label("source_id"),
        ).group_by(Contact.source_id)
        result = await db_session.execute(stmt)
        rows = result.mappings().all()
        return rows


async def init_db():
    """
    Автоматически создавать таблицы базы данных, если они не существуют
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
