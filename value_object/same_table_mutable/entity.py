from dataclasses import dataclass
from decimal import Decimal
from typing import NewType, Optional, Protocol, Text
from uuid import UUID

Currency = NewType('Currency', Text)


@dataclass
class Money:
    amount: Decimal
    currency: Currency


@dataclass
class Subscription:
    id: UUID
    name: Text
    fee: Money


class Repository(Protocol):
    def create(self, name: Text, fee: Money) -> Subscription:
        ...

    def find(self, name: Text) -> Optional[Subscription]:
        ...

    def save(self, dto: Subscription) -> None:
        ...
