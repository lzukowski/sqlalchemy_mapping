from dataclasses import dataclass, asdict
from typing import Text, Union


@dataclass(frozen=True)
class AmazonId:
    asin: Text
    sku: Text
    site: Text
    merchant_id: Text
    asdict = asdict


@dataclass(frozen=True)
class CDiscountId:
    sku: Text
    user_id: int
    asdict = asdict


@dataclass(frozen=True)
class EbayId:
    item_id: Text
    sku: Text
    asdict = asdict


Identity = Union[AmazonId, CDiscountId, EbayId]
