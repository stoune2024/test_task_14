from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Float,
    Text,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.types import JSON

Base = declarative_base()


class OperatorSourceWeight(Base):
    __tablename__ = "operator_source_weights"
    operator_id = Column(
        Integer, ForeignKey("operators.id", ondelete="CASCADE"), primary_key=True
    )
    source_id = Column(
        Integer, ForeignKey("sources.id", ondelete="CASCADE"), primary_key=True
    )
    weight = Column(Float, nullable=False, default=0.0)


class Operator(Base):
    __tablename__ = "operators"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    max_concurrent = Column(Integer, default=5, nullable=False)

    # Связь с таблицей sources через веса
    source_weights = relationship(
        "OperatorSourceWeight", backref="operator", cascade="all, delete-orphan"
    )

    # Связь с таблицей contacts (backref from Contact.operator)
    contacts = relationship("Contact", back_populates="operator")


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(
        String(100), unique=True, nullable=False
    )  # Уникальный идентификатор, например bot_telegram
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    source_weights = relationship(
        "OperatorSourceWeight", backref="source", cascade="all, delete-orphan"
    )
    contacts = relationship("Contact", back_populates="source")


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(
        String(200), nullable=True, index=True
    )  # внешний id от бота, если есть
    phone = Column(String(50), nullable=True, index=True)
    email = Column(String(200), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    contacts = relationship("Contact", back_populates="lead")

    __table_args__ = (
        # можно добавить ограничения уникальности при желании, но внешние данные часто нестроги
        (),
    )


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(
        Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False
    )
    source_id = Column(
        Integer, ForeignKey("sources.id", ondelete="SET NULL"), nullable=False
    )
    operator_id = Column(
        Integer, ForeignKey("operators.id", ondelete="SET NULL"), nullable=True
    )
    status = Column(
        String(50), nullable=False, default="new"
    )  # new, assigned, in_progress, closed
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    lead = relationship("Lead", back_populates="contacts")
    source = relationship("Source", back_populates="contacts")
    operator = relationship("Operator", back_populates="contacts")
