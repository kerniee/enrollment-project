from datetime import datetime, timezone
from math import floor
from typing import List, Union

from dateutil import parser
from pydantic import BaseModel, UUID4, NonNegativeInt, validator, errors

from market.db.schema import ShopUnitType


class ShopUnitImportBase(BaseModel):
    id: UUID4
    name: str
    parentId: Union[UUID4, None]


class ShopUnitImportItem(ShopUnitImportBase):
    type: ShopUnitType
    price: NonNegativeInt

    @validator('type')
    def must_be_offer(cls, v):
        assert v == ShopUnitType.offer
        return v


class ShopUnitImportCategory(ShopUnitImportBase):
    type: ShopUnitType
    price: None = None

    @validator('price')
    def must_be_null(cls, v):
        assert v is None
        return v

    @validator('type')
    def must_be_category(cls, v):
        assert v == ShopUnitType.category
        return v


ShopUnitImport = Union[ShopUnitImportItem, ShopUnitImportCategory]


class UTCdatetime(datetime):
    @classmethod
    def __get_validators__(cls):
        yield cls.ensureISO

    @classmethod
    def ensureISO(cls, v):
        if isinstance(v, datetime):
            return v
        try:
            date = parser.isoparse(v)
            date = date.astimezone(timezone.utc)
            date = date.replace(tzinfo=None)
            return date
        except Exception:
            raise errors.DateTimeError()


class ShopUnitItem(ShopUnitImportItem):
    date: UTCdatetime
    children: None = None

    class Config:
        orm_mode = True


class ShopUnitCategory(ShopUnitImportCategory):
    date: UTCdatetime
    price: int
    children: List[Union[ShopUnitItem, 'ShopUnitCategory']]

    @validator('price')
    def must_be_null(cls, v):
        return v


ShopUnit = Union[ShopUnitCategory, ShopUnitItem]


class ShopUnitImportRequest(BaseModel):
    items: List[ShopUnitImport]
    updateDate: UTCdatetime


class ShopUnitItemStatistics(ShopUnitImportItem):
    date: UTCdatetime
    price: float

    @validator('price')
    def floor_price(cls, v):
        return floor(v)

    @validator('type')
    def must_be_offer(cls, v):
        return v

    class Config:
        orm_mode = True


class ShopUnitStatisticResponse(BaseModel):
    items: List[ShopUnitItemStatistics]
