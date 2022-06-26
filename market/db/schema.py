from enum import Enum, unique

from sqlalchemy import (
    Column, Enum as PgEnum, ForeignKey, String, DateTime, Float, Integer
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from market.db.base import Base


@unique
class ShopUnitType(Enum):
    category = 'CATEGORY'
    offer = 'OFFER'


class ShopUnitMixin:
    name = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)

    type = Column(PgEnum(ShopUnitType, name='type'), nullable=False)
    price = Column(Float, nullable=False, default=0)


class ShopUnit(ShopUnitMixin, Base):
    __tablename__ = 'shop_units'
    id = Column(UUID(as_uuid=True), primary_key=True)

    parentId = Column(UUID(as_uuid=True), ForeignKey('shop_units.id'), nullable=True)

    parent = relationship('ShopUnit', remote_side=[id], back_populates='children')
    children = relationship('ShopUnit', cascade="all,delete", back_populates='parent')
    children_count = Column(Integer, nullable=True, default=0)

    statistics_children = relationship("ShopUnitStatistics", cascade="all,delete", backref="newest_unit")


class ShopUnitStatistics(ShopUnitMixin, Base):
    __tablename__ = 'shop_units_statistics'

    id = Column(UUID(as_uuid=True), ForeignKey(ShopUnit.id), primary_key=True)

    parentId = Column(UUID(as_uuid=True), nullable=True)
    date = Column(DateTime, primary_key=True)
