from typing import Tuple, Iterator
from unittest import TestCase

from factory import Factory, Iterator as IteratorFactory
from factory.fuzzy import FuzzyInteger, FuzzyText
from sqlalchemy.orm import sessionmaker

from db import memory_engine, metadata
from .acl import Acl
from .platform import AmazonId, CDiscountId, EbayId, Identity


class AmazonIdFactory(Factory):
    class Meta:
        model = AmazonId

    asin = FuzzyText()
    sku = FuzzyText()
    site = IteratorFactory(['GB', 'US', 'PL', 'FR', 'CN', 'DE'])
    merchant_id = FuzzyText()


class CDiscountIdFactory(Factory):
    class Meta:
        model = CDiscountId

    sku = FuzzyText()
    user_id = FuzzyInteger(999, 9999)


class EbayIdFactory(Factory):
    class Meta:
        model = EbayId

    item_id = FuzzyText()
    sku = FuzzyText()


class TestAcl(TestCase):
    def setUp(self) -> None:
        metadata.create_all(memory_engine)
        self.session = sessionmaker(bind=memory_engine)()
        self.acl = Acl(self.session)

    def tearDown(self) -> None:
        metadata.drop_all(memory_engine)

    def test_find_id_by_amazon_identity(self):
        for mapped_id, identity in self.identities():
            self.assertEqual(self.acl.get_id(identity), mapped_id)

    def test_find_identity_by_id(self):
        for mapped_id, identity in self.identities():
            found, = self.acl.get_identity(mapped_id)
            self.assertEqual(found, identity)

    def identities(self) -> Iterator[Tuple[int, Identity]]:
        identities = {
            'Amazon': AmazonIdFactory(),
            'CDiscount': CDiscountIdFactory(),
            'Ebay': EbayIdFactory(),
        }

        for i, (platform, identity) in enumerate(identities.items()):
            with self.subTest(platform):
                self.acl.add(i, identity)
                yield i, identity
