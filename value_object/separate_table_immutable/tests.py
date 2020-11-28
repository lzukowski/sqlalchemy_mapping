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
AMOUNT_C = model.fee_table.c.amount
CURRENCY_C = model.fee_table.c.currency


class TestMutableSeparateTableMapping(TestCase):
    def setUp(self) -> None:
        metadata.create_all(memory_engine)
        self.session = sessionmaker(bind=memory_engine)()
        self.repository = model.Repository(self.session)

    def tearDown(self) -> None:
        metadata.drop_all(memory_engine)

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

    def test_not_duplicating_fees_when_changing_value(self):
        subscription = self.given_active_subscription()
        self.repository.save(subscription)

        subscription.fee = Money(Decimal('11.3'), Currency('PLN'))
        self.repository.save(subscription)

        newest_fee = Money(Decimal('45.3'), Currency('PLN'))
        subscription.fee = newest_fee
        self.repository.save(subscription)

        number_of_stored_fees = self.session.query(model.Fee).count()
        self.assertEqual(number_of_stored_fees, 1)
        db_fee = self.session.query(model.Fee).one()

        assert db_fee == newest_fee
        self.assertAlmostEqual(db_fee, newest_fee)

    def test_deletes_fee_when_deleting_subscription(self):
        subscription = self.given_active_subscription()
        self.repository.save(subscription)

        self.session.delete(subscription)

        number_of_stored_fees = self.session.query(model.Fee).count()
        self.assertEqual(number_of_stored_fees, 0)

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
        self.session.expire_all()
        query = (
            self.session.query(*columns)
            .join(TABLE, TABLE.c.fee_id == model.fee_table.c.id)
            .filter(TABLE.c.id == subscription_id)
        )
        return query.one()
