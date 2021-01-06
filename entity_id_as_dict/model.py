from __future__ import annotations

import hashlib
import json
from enum import Enum

import sqlalchemy as sa
from sqlalchemy.ext.hybrid import Comparator, hybrid_property

from db import Base
from .platform import AmazonId, CDiscountId, EbayId, Identity


class Mapping(Base):
    __tablename__ = 'mappings'
    __table_args__ = (
        sa.UniqueConstraint('platform', 'digest', name='platform_identity'),
    )

    class Platform(Enum):
        AMAZON = 'Amazon'
        EBAY = 'eBay'
        CDISCOUNT = 'CDiscount'

    id = sa.Column(sa.BigInteger, primary_key=True)
    _platform = sa.Column('platform', sa.Enum(Platform), nullable=False)
    _dict = sa.Column('identity', sa.JSON, nullable=False)
    _digest = sa.Column('digest', sa.VARBINARY(16), nullable=False)

    @classmethod
    def get_platform(cls, identity: Identity) -> Platform:
        if isinstance(identity, AmazonId):
            return Mapping.Platform.AMAZON
        elif isinstance(identity, CDiscountId):
            return Mapping.Platform.CDISCOUNT
        elif isinstance(identity, EbayId):
            return Mapping.Platform.EBAY
        raise NotImplementedError(identity)

    @classmethod
    def digest(cls, identity: Identity) -> bytes:
        identity_json = json.dumps(
            identity.asdict(), sort_keys=True,
        ).encode("utf-8")
        return hashlib.md5(identity_json).digest()

    @hybrid_property
    def identity(self) -> Identity:
        if self._platform == Mapping.Platform.AMAZON:
            return AmazonId(**self._dict)
        elif self._platform == Mapping.Platform.CDISCOUNT:
            return CDiscountId(**self._dict)
        elif self._platform == Mapping.Platform.EBAY:
            return EbayId(**self._dict)
        else:
            raise NotImplementedError(self._platform)

    @identity.setter
    def identity(self, value: Identity) -> None:
        self._platform = self.get_platform(value)
        self._dict = value.asdict()
        self._digest = self.digest(value)

    @identity.comparator
    def identity(self) -> Mapping.IdentityComparator:
        return Mapping.IdentityComparator(self._digest)

    class IdentityComparator(Comparator):
        def __eq__(self, other: Identity) -> bool:
            other_digest = Mapping.digest(other)
            return self.__clause_element__() == other_digest
