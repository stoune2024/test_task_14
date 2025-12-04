from typing import List

from app.routers import crm_router
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    OperatorCreate,
    OperatorUpdate,
    OperatorOut,
    SourceCreate,
    SourceOut,
    OperatorSourceWeightCreate,
    ContactCreate,
    ContactOut,
)
from app.repository import (
    get_session,
    get_session_sync,
    OperatorRepository,
    SourceRepository,
    WeightRepository,
    ContactRepository,
    LeadRepository,
)


@crm_router.post("/operators", response_model=OperatorOut)
async def create_operator(
    data: OperatorCreate, db_session: AsyncSession = Depends(get_session)
):
    """
    Эндпоинт создания оператора
    :param data: информация об операторе
    :param db_session: асинхронная сессия БД
    :return: модель OperatorOut
    """
    try:
        return await OperatorRepository.create(
            db_session,
            name=data.name,
            is_active=data.is_active,
            max_concurrent=data.max_concurrent,
        )
    except Exception as e:
        return {"error": e}


@crm_router.get("/operators", response_model=list[OperatorOut])
async def list_operators(db_session: AsyncSession = Depends(get_session)):
    """
    Эндпоинт просмотра списка операторов
    :param db_session: сессия БД
    :return: список операторов
    """
    try:
        return await OperatorRepository.get_all(db_session)
    except Exception as e:
        return {"error": e}


@crm_router.patch("/operators/{operator_id}", response_model=OperatorOut)
async def update_operator(
    operator_id: int,
    data: OperatorUpdate,
    db_session: AsyncSession = Depends(get_session),
):
    """
    Эндпоинт управления лимитом нагрузки и активностью оператора
    :param operator_id: идентификатор оператора
    :param data: информация для обновления
    :param db_session: сессия БД
    :return: модель OperatorOut
    """
    try:
        op = await OperatorRepository.update(db_session, data, operator_id=operator_id)
        if not op:
            raise HTTPException(status_code=404, detail="Operator not found")
        return op
    except Exception as e:
        return {"error": e}


@crm_router.post("/sources", response_model=SourceOut)
async def create_source(
    data: SourceCreate, db_session: AsyncSession = Depends(get_session)
):
    """
    Эндпоинт создания источника (бота)
    :param data: информация об источнике
    :param db_session: сессия БД
    :return: модель SourceOut
    """
    try:
        return await SourceRepository.create(
            db_session, name=data.name, code=data.code, description=data.description
        )
    except Exception as e:
        return {"error": e}


@crm_router.post("/sources/{source_id}")
async def distribute_weights_for_source(
    source_id: int,
    weights: List[OperatorSourceWeightCreate],
    db_session: AsyncSession = Depends(get_session),
):
    """
    Эндпоинт настройки для источника списка операторов и их весов.
    ВАЖНО: эндпоинт удаляет все старые записи из ассоциативной таблицы OperatorSourceWeight для конкретного источника (перезаписывает для него).
    Это выполнено с целью упрощения логики.

    :param source_id: идентификатор источника
    :param weights: информация об операторах и весах (список ассоциативных таблиц)
    :param db_session: сессия БД
    :return: сообщение
    """
    try:
        await WeightRepository.set_weights(db_session, source_id, weights)
        return {"message": "ok"}
    except Exception as e:
        return {"error": e}


@crm_router.post("/contacts/{source_code}", response_model=ContactOut)
async def create_contact(
    data: ContactCreate,
    source_code: str,
    db_session: AsyncSession = Depends(get_session_sync),
):
    """
    Эндпоинт, отвечающий за соблюдение бизнес логики маршрутизации обращений
    :param data: информацтя
    :param db_session: синхронная сессия БД
    :return: модель ContactOut
    """
    contact_out = await ContactRepository.create(
        data,
        db_session,
        source_code,
    )
    return contact_out


@crm_router.get("/contacts_and_leads", response_model=list[ContactOut])
async def list_contacts(db_session: AsyncSession = Depends(get_session)):
    """
    Эндпоинт для просмотра списка лидов и их обращений
    :param lead_id:
    :param db_session:
    :return:
    """
    # db_session.execute(Customer.id, Customer.username, Order.id).join(Order).all()

    # s = select(
    #             orders.c.id,
    #             orders.c.date_placed
    # ).select_from(
    #     orders.join(customers)
    # ).where(
    #     and_(
    #         customers.c.first_name == "Vladimir",
    #         customers.c.last_name == "Belousov",
    #     )
    # )

    return await LeadRepository.get_by_lead_id(db_session, lead_id)
