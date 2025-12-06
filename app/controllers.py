from typing import List, Optional, Any, Dict

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
    LeadsAndContactsOut,
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

"""
Слой FastAPI эндпоинтов
"""


@crm_router.post(
    "/operators",
    response_model=OperatorOut,
    summary="Создать оператора",
    description="Эндпоинт добавляет оператора в базу данных",
)
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
        raise HTTPException(status_code=400, detail=str(e))


@crm_router.get(
    "/operators",
    response_model=List[OperatorOut],
    summary="Просмотр операторов",
    description="Эндпоинт просмотра списка операторов из БД",
)
async def list_operators(db_session: AsyncSession = Depends(get_session)):
    """
    Эндпоинт просмотра списка операторов
    :param db_session: сессия БД
    :return: список операторов
    """
    try:
        return await OperatorRepository.get_all(db_session)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@crm_router.patch(
    "/operators/{operator_id}",
    response_model=OperatorOut,
    summary="Обновить оператора",
    description="Эндпоинт управления лимитом нагрузки и активностью оператора",
)
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
        raise HTTPException(status_code=400, detail=str(e))


@crm_router.post(
    "/sources",
    response_model=SourceOut,
    summary="Добавить источник",
    description="Эндпоинт добавления информации об источнике в БД",
)
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
        raise HTTPException(status_code=400, detail=str(e))


@crm_router.post(
    "/sources/{source_id}",
    response_model=Dict[str, str],
    summary="Определить веса для источника",
    description="Эндпоинт позволяет настроить для конкретного источника список операторов и их веса по отношению к этому источнику",
)
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
        raise HTTPException(status_code=400, detail=str(e))


@crm_router.post(
    "/contacts/{source_code}",
    response_model=ContactOut,
    summary="Создать обращение",
    description="Эндпоинт создания обращении на основе алгоритма распределения обращения (см. README)",
)
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
    try:
        contact_out = await ContactRepository.create(
            data,
            db_session,
            source_code,
        )
        return contact_out
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@crm_router.get(
    "/contacts_and_leads",
    response_model=List[LeadsAndContactsOut],
    summary="Просмотр обращений",
    description="Эндпоинт просмотра списка лидов и их обращений",
)
async def list_contacts(db_session: AsyncSession = Depends(get_session)):
    """
    Эндпоинт для просмотра списка лидов и их обращений
    :param db_session: сессия БД
    :return: список моделей LeadsAndContactsOut
    """
    try:
        return await LeadRepository.get_leads_and_contacts(db_session)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@crm_router.get(
    "/contacts_by_operators",
    response_model=List[Dict[str, Optional[int]]],
    summary="Просмотр распределения обращений по оператором",
    description="Эндпоинт просмотра распределения обращений по операторам",
)
async def group_contacts_by_operators(
    db_session: AsyncSession = Depends(get_session),
) -> Optional[List[Dict[Any, Any]]]:
    """
    Эндпоинт отображения распределения обращений по операторам
    :param db_session: сессия БД
    :return: список словарей с парами количество_контактов:идентификатор_оператора
    """
    try:
        return await ContactRepository.get_operator_stats(db_session)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@crm_router.get(
    "/contacts_by_sources",
    response_model=List[Dict[str, Optional[int]]],
    summary="Просмотр распределния обращений по источникам",
    description="Эндпоинт просмотра распределения обращений по источникам",
)
async def group_contacts_by_sources(
    db_session: AsyncSession = Depends(get_session),
) -> Optional[List[Dict[Any, Any]]]:
    """
    Эндпоинт отображения распределения обращений по источникам
    :param db_session: сессия БД
    :return: список словарей с парами количество_контактов:идентификатор_источника
    """
    try:
        return await ContactRepository.get_source_stats(db_session)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
