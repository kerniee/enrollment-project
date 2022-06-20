from enum import Enum, unique

from sqlalchemy import (
    Column, Date, Enum as PgEnum, ForeignKey, Integer, String
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from market.db.base import Base


@unique
class ShopUnitType(Enum):
    category = 'CATEGORY'
    offer = 'OFFER'


class ShopUnit(Base):
    __tablename__ = 'shop_units'

    id = Column(UUID, primary_key=True)
    name = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    parentId = Column(UUID, ForeignKey('shop_units.id'), nullable=True)
    type = Column(PgEnum(ShopUnitType, name='type'), nullable=False)
    price = Column(Integer, nullable=True)

    parent = relationship('ShopUnit', remote_side=[id], backref='children')
