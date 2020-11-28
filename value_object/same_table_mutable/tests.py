from decimal import Decimal
from random import choice, randrange
from typing import Tuple
from unittest.case import TestCase
from uuid import UUID, uuid1

from sqlalchemy import Column
from sqlalchemy.orm import sessionmaker

from . import model
from db import memory_engine, metadata
from .entity import Currency, Money, Subscription

TABLE = model.Subscription.__table__
AMOUNT_C = TABLE.c.fee_amount
CURRENCY_C = TABLE.c.fee_currency


class TestMutableMapping(TestCase):
    def setUp(self) -> None:
        metadata.create_all(memory_engine)
        self.session = sessionmaker(bind=memory_engine)()
        self.repository = model.Repository(self.session)

    def tearDown(self) -> None:
        metadata.drop_all(memory_engine)

    def test_change_money_amount(self) -> None:
        subscription = self.given_active_subscription()

        new_amount = Decimal('30.7')
        subscription.fee.amount = new_amount
        self.repository.save(subscription)

        db_amount, = self.get_db_values(subscription.id, AMOUNT_C)
        self.assertAlmostEqual(db_amount, new_amount)

    def test_change_money_currency(self) -> None:
        subscription = self.given_active_subscription()

        subscription.fee.currency = 'PLN'
        self.repository.save(subscription)

        db_currency, = self.get_db_values(subscription.id, CURRENCY_C)
        self.assertEqual(db_currency, 'PLN')

    def test_change_whole_value_object(self) -> None:
        subscription = self.given_active_subscription()

        new_fee = Money(Decimal('11.3'), Currency('PLN'))
        subscription.fee = new_fee
        self.repository.save(subscription)

        db_amount, db_currency = self.get_db_values(
            subscription.id, AMOUNT_C, CURRENCY_C,
        )
        self.assertAlmostEqual(float(db_amount), float(new_fee.amount))
        self.assertEqual(db_currency, new_fee.currency)

    def test_copy_value_from_other_subscription(self) -> None:
        subscription = self.given_active_subscription()
        other = self.given_active_subscription()

        subscription.fee = other.fee
        self.repository.save(subscription)

        db_amount, db_currency = self.get_db_values(
            subscription.id, AMOUNT_C, CURRENCY_C,
        )
        self.assertAlmostEqual(float(db_amount), float(other.fee.amount))
        self.assertEqual(db_currency, other.fee.currency)

    def given_active_subscription(self) -> Subscription:
        fee = Money(
            amount=Decimal(randrange(1000, 53400)/100),
            currency=choice([Currency('EUR'), Currency('GBP'), Currency('USD')])
        )
        name = uuid1().hex
        subscription = self.repository.create(name, fee)
        self.repository.save(subscription)
        return subscription

    def get_db_values(self, subscription_id: UUID, *columns: Column) -> Tuple:
        self.session.expunge_all()
        query = (
            self.session.query(*columns)
            .filter(TABLE.c.id == subscription_id)
        )
        return query.one()
