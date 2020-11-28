from datetime import datetime
from typing import Any, Optional, Text
from uuid import uuid1

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
)
from sqlalchemy.event import listens_for
from sqlalchemy.orm import relationship, Session
from sqlalchemy.orm.attributes import Event
from sqlalchemy_utils import CurrencyType, UUIDType

from db import Base
from . import entity


class Fee(entity.Money, Base):
    __table__: Table
    __tablename__ = 'mutable_separate_vo_fees'

    id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(Float(asdecimal=True), nullable=False)
    currency = Column(CurrencyType, nullable=False)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, entity.Money):
            return NotImplemented
        same_amount = self.amount == other.amount
        same_currency = self.currency == other.currency
        return same_amount and same_currency


class Subscription(entity.Subscription, Base):
    __table__: Table
    __tablename__ = 'mutable_separate_vo_subscription_plans'

    id = Column(UUIDType(binary=True), primary_key=True)
    name = Column(String(100), nullable=False, index=True, unique=True)
    when_created = Column(DateTime, nullable=False, default=datetime.utcnow)
    when_updated = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    fee_id = Column(Integer, ForeignKey(Fee.id), nullable=False)
    fee = relationship(
        Fee, cascade='save-update,merge,delete,delete-orphan', uselist=False,
        single_parent=True, backref='subscription',
    )


@listens_for(Subscription.fee, 'set', retval=True)
def convert_money_to_fee_on_set(
        t: Subscription, value: entity.Money, old: Optional[Fee], e: Event,
) -> Fee:
    if old is None:
        return Fee(value.amount, value.currency)
    else:
        old.amount = value.amount
        old.currency = value.currency
        return old


class Repository(entity.Repository):
    def __init__(self, session: Session) -> None:
        self._session = session
        self.query = session.query(Subscription)

    def create(self, name: Text, fee: entity.Money) -> Subscription:
        return Subscription(id=uuid1(), name=name, fee=fee)

    def find(self, name: Text) -> Optional[entity.Subscription]:
        return self.query.with_for_update().filter_by(name=name).one_or_none()

    def save(self, model: Subscription) -> None:
        self._session.add(model)
        try:
            self._session.commit()
        except:
            self._session.rollback()
            raise


table = Subscription.__table__
fee_table = Fee.__table__
__all__ = ['Repository', 'table', 'fee_table']
