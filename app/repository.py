# app/repository.py

"""
Слой доступа к данным для службы ведущего маршрутизатора.
Использует SQLAlchemy AsyncSession для операций с базой данных.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    OperatorCreate,
    OperatorOut,
    LeadOut,
    LeadCreate,
    SourceCreate,
    SourceOut,
    OperatorSourceWeightCreate,
    ContactCreate,
    ContactOut,
)
from app.schemas import Operator, Lead, Source, OperatorSourceWeight, Contact


class OperatorRepository:
    """
    Класс для взаимодействия с сущностью Operator
    """

    async def create(
        self, db: AsyncSession, *, name: str, is_active: bool, max_concurrent: int
    ) -> OperatorOut:
        """
        Функция создания оператора
        :param db: сессия БД
        :param name: имя оператора
        :param is_active: активен ли оператор
        :param max_concurrent: максимальная нагрузка оператора
        :return: модель OperatorOut
        """
        operator = OperatorCreate(
            name=name, is_active=is_active, max_concurrent=max_concurrent
        )
        db.add(operator)
        await db.commit()
        await db.refresh(operator)
        operator_out = OperatorOut.model_validate(operator)
        return operator_out

    async def get_all(self, db: AsyncSession) -> List[OperatorOut]:
        """
        Функция возврата всех операторов
        :param db: сессия БД
        :return: список моделей OperatorOut
        """
        result = await db.execute(select(Operator))
        list_of_operators = []
        for i in result.scalars().all():
            operator_out = OperatorOut.model_validate(i)
            list_of_operators.append(operator_out)
        return list_of_operators

    async def get(self, db: AsyncSession, operator_id: int) -> Optional[OperatorOut]:
        """
        Функция возврата оператора по его operator_id
        :param db: сессия ДБ
        :param operator_id: идентификатор оператора
        :return: модель OperatorOut
        """
        operator = await db.get(Operator, operator_id)
        operator_out = OperatorOut.model_validate(operator)
        return operator_out

    async def update(
        self,
        db: AsyncSession,
        operator: Operator,
        *,
        is_active: Optional[bool] = None,
        max_concurrent: Optional[int] = None,
    ) -> OperatorOut:
        """
        Функция обновления конкретного оператора
        :param db: сессия БД
        :param operator: объект Operator из БД
        :param is_active: активен ли оператор
        :param max_concurrent: максимальнеая нагрузка
        :return: модель OperatorOut
        """
        if is_active is not None:
            operator.is_active = is_active
        if max_concurrent is not None:
            operator.max_concurrent = max_concurrent
        await db.commit()
        await db.refresh(operator)
        operator_out = OperatorOut.model_validate(operator)
        return operator_out


class LeadRepository:
    """
    Класс для взаимодействия с сущностью Lead
    """

    async def get_by_external_id(
        self, db: AsyncSession, external_id: str
    ) -> Optional[LeadOut]:
        """
        Функция получения лида по идентификатору источника
        :param db: сессия ДБ
        :param external_id: идентификатор внешнего источника
        :return: модель LeadOut
        """
        result = await db.execute(select(Lead).where(Lead.external_id == external_id))
        lead_out = LeadOut.model_validate(result.scalars().first())
        return lead_out

    async def create(self, db: AsyncSession, *, external_id: str) -> LeadOut:
        """
        Функция создания лида
        :param db: сессия ДБ
        :param external_id: идентификатор внешнего источника
        :return: модель LeadOut
        """
        lead = LeadCreate(external_id=external_id)
        db.add(lead)
        await db.commit()
        await db.refresh(lead)
        lead_out = LeadOut.model_validate(lead)
        return lead_out


class SourceRepository:
    """
    Класс для взаимодействия с сущностью Source
    """

    async def create(self, db: AsyncSession, *, name: str, code: str) -> SourceOut:
        """
        Функция создания источника
        :param db: сессия БД
        :param name: названия источника
        :param code: уникальный идентификатор источника
        :return: модель SourceOut
        """
        source = SourceCreate(name=name, code=code)
        db.add(source)
        await db.commit()
        await db.refresh(source)
        source_out = SourceOut.model_validate(source)
        return source_out

    async def get(self, db: AsyncSession, source_id: int) -> Optional[SourceOut]:
        """
        Функиця возврата источника по его source_id
        :param db: сессия БД
        :param source_id: целочисленный идентфиикатор источника
        :return: модель SourceOut
        """
        source = await db.get(Source, source_id)
        source_out = SourceOut.model_validate(source)
        return source_out


class WeightRepository:
    """
    Класс для взаимодействия с сущностью Weight
    """

    async def set_weights(
        self,
        db: AsyncSession,
        *,
        source_id: int,
        weights: List[OperatorSourceWeightCreate],
    ):
        """
        Функция установки весов операторов по конкретному источнику по его source_id
        :param db: сессия БД
        :param source_id: идентификатор источника
        :param weights: список моделей OperatorSourceWeightCreate
        :return: None
        """
        # Удаляем старые веса
        result = await db.execute(
            select(OperatorSourceWeight).where(
                OperatorSourceWeight.source_id == source_id
            )
        )
        for w in result.scalars().all():
            await db.delete(w)

        # Добавляем новые веса
        for w in weights:
            db.add(
                OperatorSourceWeightCreate(
                    source_id=source_id,
                    operator_id=w.operator_id,
                    weight=w.weight,
                )
            )

        await db.commit()

    async def get_for_source(
        self, db: AsyncSession, source_id: int
    ) -> List[OperatorSourceWeightCreate]:
        """
        Функция получения списка операторов и их весов по конкретному источнику по его source_id
        :param db: сессия ДБ
        :param source_id: идентфикатор источника
        :return:
        """
        result = await db.execute(
            select(OperatorSourceWeight).where(
                OperatorSourceWeight.source_id == source_id
            )
        )
        operator_source_weights_list = []
        for i in result.scalars().all():
            data_out = OperatorSourceWeightCreate.model_validate(i)
            operator_source_weights_list.append(data_out)
        return operator_source_weights_list


class ContactRepository:
    """
    Класс для взаимодействия с сущностью Contact
    """

    async def create(
        self,
        db: AsyncSession,
        *,
        lead_id: int,
        source_id: int,
        operator_id: Optional[int],
    ) -> ContactOut:
        """
        Функция создания контакта
        :param db: сессия БД
        :param lead_id: идентификатор лида
        :param source_id: идентификатор источника
        :param operator_id: идентификатор оператора
        :return: модель ContactOut
        """
        contact = ContactCreate(
            lead_id=lead_id, source_id=source_id, operator_id=operator_id
        )
        db.add(contact)
        await db.commit()
        await db.refresh(contact)
        contact_out = ContactOut.model_validate(contact)
        return contact_out

    async def get_all_for_lead(
        self, db: AsyncSession, lead_id: int
    ) -> List[ContactOut]:
        """
        Функция возврата всех контактов по лиду по его lead_id
        :param db: сессия БД
        :param lead_id: идентификатор лида
        :return: список моделей ContactOut
        """
        result = await db.execute(select(Contact).where(Contact.lead_id == lead_id))
        contact_out_list = []
        for i in result.scalars().all():
            contact_out = ContactOut.model_validate(i)
            contact_out_list.append(contact_out)
        return contact_out_list
