from datetime import datetime
from decimal import Decimal
from typing import Optional, Text
from uuid import uuid1

from sqlalchemy import Column, DateTime, Float, String, Table
from sqlalchemy.orm import Session
from sqlalchemy_utils import CurrencyType, UUIDType

from db import Base
from . import entity


class Subscription(entity.Subscription, Base):
    __table__: Table
    __tablename__ = 'immutable_property_vo_subscription_plans'

    id = Column(UUIDType(binary=True), primary_key=True)
    name = Column(String(100), nullable=False, index=True, unique=True)
    when_created = Column(DateTime, nullable=False, default=datetime.utcnow)
    when_updated = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    _fee_amount = Column('fee_amount', Float(asdecimal=True), nullable=False)
    _fee_currency = Column('fee_currency', CurrencyType, nullable=False)

    @property
    def fee(self) -> entity.Money:
        return entity.Money(Decimal(self._fee_amount), self._fee_currency)

    @fee.setter
    def fee(self, value: entity.Money) -> None:
        self._fee_amount = value.amount
        self._fee_currency = value.currency

    def __hash__(self):
        return hash(self.id)


class Repository(entity.Repository):
    def __init__(self, session: Session) -> None:
        self._session = session
        self.query = session.query(Subscription)

    def create(self, name: Text, fee: entity.Money) -> Subscription:
        return Subscription(id=uuid1(), name=name, fee=fee)

    def find(self, name: Text) -> Optional[entity.Subscription]:
        return self.query.with_for_update().filter_by(name=name).one_or_none()

    def save(self, model: Subscription) -> None:
        self._session.merge(model)
        try:
            self._session.commit()
        except:
            self._session.rollback()
            raise


table = Subscription.__table__
__all__ = ['Repository', 'table']
