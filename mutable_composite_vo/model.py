from datetime import datetime
from decimal import Decimal
from typing import Any, Optional, Text, Tuple
from uuid import uuid1

from sqlalchemy import Column, DateTime, Float, String, Table
from sqlalchemy.ext.mutable import MutableComposite
from sqlalchemy.orm import composite, Session
from sqlalchemy_utils import CurrencyType, UUIDType

from db import Base
from . import entity


class Money(entity.Money, MutableComposite):
    def __composite_values__(self) -> Tuple[Decimal, entity.Currency]:
        return self.amount, self.currency

    def __setattr__(self, key: Text, value: Any) -> None:
        super().__setattr__(key, value)
        self.changed()

    @classmethod
    def coerce(cls, key: Text, value: entity.Money) -> 'Money':
        return Money(value.amount, value.currency)

    def __eq__(self, other: entity.Money) -> bool:
        same_amount = self.amount == other.amount
        same_currency = self.currency == other.currency
        return same_amount and same_currency


class Subscription(entity.Subscription, Base):
    __table__: Table
    __tablename__ = 'mutable_composite_vo_subscription_plans'

    id = Column(UUIDType(binary=True), primary_key=True)
    name = Column(String(100), nullable=False, index=True, unique=True)
    when_created = Column(DateTime, nullable=False, default=datetime.utcnow)
    when_updated = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    fee = composite(
        Money,
        Column('fee_amount', Float(asdecimal=True), nullable=False),
        Column('fee_currency', CurrencyType, nullable=False),
    )

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
