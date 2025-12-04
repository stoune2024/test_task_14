from sqlalchemy.orm import Session
from typing import Optional, List, Dict
import random
from pydantic import EmailStr

from app.schemas import Lead, Operator, Contact, Source, OperatorSourceWeight
from app.models import LeadOut

"""
Бизнес-логика для маршрутизации CRM: идентификация потенциальных клиентов, доступность оператора,
взвешенная маршрутизация и создание контактов.

Предполагает синхронную работу SQLAlchemy и таблиц из schemas.py.
"""


class LeadService:
    """
    Класс для осуществления бизнес логики определения лида
    """

    @staticmethod
    def find_or_create_lead(
        db_session: Session,
        external_id: str | None,
        phone: str | None,
        email: EmailStr | None,
    ) -> Lead:
        """
        Функция поиска или создания лида, если он обращается впервые
        :param db_session: сессия БД
        :param external_id: идентификатор источника
        :param phone: номер телефона лида
        :param email: электронная почта
        :return: модель LeadOut
        """
        query = db_session.query(Lead)
        lead: Optional[Lead] = None

        if external_id:
            lead = query.filter(Lead.external_id == external_id).first()
        if not lead and phone:
            lead = query.filter(Lead.phone == phone).first()
        if not lead and email:
            lead = query.filter(Lead.email == email).first()

        if lead:
            return lead

        # Лида не нашли - создаем
        new_lead = Lead(
            external_id=external_id,
            phone=phone,
            email=email,
        )
        db_session.add(new_lead)
        db_session.commit()
        new_lead_out = LeadOut(
            id=new_lead.id,
            external_id=new_lead.external_id,
            phone=new_lead.phone,
            email=new_lead.email,
        )
        db_session.refresh(new_lead)
        return new_lead_out


class OperatorService:
    """
    Класс для осуществления бизнес логики определения оператора
    """

    @staticmethod
    def get_operator_load(db: Session, operator_id: int) -> int:
        """
        Функция определения нагрузки оператора по его идентификатору
        :param db: сессия БД
        :param operator_id: идентификатор оператора
        :return: Текущая нагрузка оператора
        """
        return (
            db.query(Contact)
            .filter(
                Contact.operator_id == operator_id,
                Contact.status.in_(["assigned", "in_progress"]),
            )
            .count()
        )

    @staticmethod
    def eligible_operators_for_source(db: Session, source: Source) -> List[Operator]:
        """
        Приемлимые операторы для источника
        :param db: сессия БД
        :param source: объект типа Source
        :return: список операторов Operator
        """
        # Операторы, связанные с источниками через веса
        links = (
            db.query(OperatorSourceWeight)
            .filter(OperatorSourceWeight.source_id == source.id)
            .all()
        )
        operator_ids = [l.operator_id for l in links]

        if not operator_ids:
            return []

        ops = db.query(Operator).filter(Operator.id.in_(operator_ids)).all()

        # Фильтруем активных и с нагрузкой, которая меньше максимальной
        eligible = []
        for op in ops:
            if not op.is_active:
                continue
            load = OperatorService.get_operator_load(db, op.id)
            if load < op.max_concurrent:
                eligible.append(op)
        return eligible

    @staticmethod
    def get_weights_for_source(db: Session, source: Source) -> Dict[int, float]:
        """
        Функция возврата операторов и их весов по отношению к источнику
        :param db: сессия БД
        :param source: источник
        :return: словарь с идентификатором операторов и их весов
        """
        rows = (
            db.query(OperatorSourceWeight)
            .filter(OperatorSourceWeight.source_id == source.id)
            .all()
        )
        return {r.operator_id: r.weight for r in rows}

    @staticmethod
    def choose_operator_weighted(
        eligible: List[Operator], weights: Dict[int, float]
    ) -> Optional[Operator]:
        """
        Функция подбора оператора
        :param eligible: список подходящих операторов
        :param weights: словарь {идентификатор оператора:вес}
        :return: наиболее подходящий оператор (модель OperatorOut)
        """
        if not eligible:
            return None

        # Извлекаем веса из списка подходящих операторов.
        ops_and_weights = {op.id: weights.get(op.id, 0) for op in eligible}
        total = sum(ops_and_weights.values())
        if total <= 0:
            # Равномерное распределение
            return random.choice(eligible)

        operators = eligible
        probs = [ops_and_weights[op.id] / total for op in operators]
        return random.choices(operators, weights=probs, k=1)[0]


class ContactService:
    """
    Класс для осуществления бизнес логики создания обращения
    """

    @staticmethod
    def create_contact(
        db: Session,
        lead: Lead,
        source: Source,
        operator: Optional[Operator],
        payload: dict | None,
    ) -> Contact:
        """
        Функция создания обращения
        :param db: сессия БД
        :param lead: Лид
        :param source: Источник
        :param operator: Оператор
        :param payload: содержимое обращения
        :return: Модель обращения ContactOut
        """
        contact = Contact(
            lead_id=lead.id,
            source_id=source.id,
            operator_id=operator.id if operator else None,
            status="assigned" if operator else "new",
            payload=payload or {},
        )

        db.add(contact)
        db.commit()
        db.refresh(contact)
        return contact


class RoutingService:
    """
    Главный класс для осуществления бизнес логики маршрутизации обращения
    """

    @staticmethod
    def route_and_create_contact(
        db_session: Session,
        external_id: str | None,
        phone: str | None,
        email: EmailStr | None,
        source_code: str,
        payload: dict | None,
    ) -> Contact:
        """
        Функция, создающая и маршрутизирующая обращение
        :param db_session: сессия БД
        :param external_id: идентификатор источника
        :param phone: номер телефона лида
        :param email: электронная почта лида
        :param source_code: уникальный идентификатор источника
        :param payload: содержимое обращения
        :return: объект-обращение Contact
        """
        # 1. Идентифицируем лида
        lead = LeadService.find_or_create_lead(
            db_session,
            external_id=external_id,
            phone=phone,
            email=email,
        )

        # 2. Определяем источник
        source = db_session.query(Source).filter(Source.code == source_code).first()
        if not source:
            raise ValueError(f"Источник не найден: {source_code}")

        # 3. Подходящие оператора
        eligible = OperatorService.eligible_operators_for_source(db_session, source)
        weights = OperatorService.get_weights_for_source(db_session, source)

        # 4. Распределение весов и получение соответствующего оператора
        operator = OperatorService.choose_operator_weighted(eligible, weights)

        # 5. Создание обращения (оператор может быть None)
        return ContactService.create_contact(
            db_session,
            lead=lead,
            source=source,
            operator=operator,
            payload=payload,
        )
