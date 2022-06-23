import logging
from datetime import datetime
from typing import Optional
from typing import Union

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from market.api.schema import ShopUnitImport
from market.db.schema import ShopUnit
from market.db.schema import ShopUnitStatistics, ShopUnitType
from market.utils.exceptions import HTTPException


async def get_shop_unit(unit_id, session: AsyncSession, for_update: bool = False) -> Optional[ShopUnit]:
    if for_update:
        result = await session.execute(select(ShopUnit).where(ShopUnit.id == unit_id).with_for_update())
    else:
        result = await session.execute(select(ShopUnit).where(ShopUnit.id == unit_id))
    return result.scalars().one_or_none()


def get_dict_from_unit(unit: Union[ShopUnit, ShopUnitImport], date, include_category_price=False) -> dict:
    values = {
        "id": unit.id,
        "name": unit.name,
        "parentId": unit.parentId,
        "type": unit.type,
        "date": date
    }
    if include_category_price or unit.type != ShopUnitType.category:
        values["price"] = unit.price
    return values


async def session_commit(session: AsyncSession):
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, message="Validation Failed")


class UnitCRUD:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_to_statistics(self, unit: ShopUnit):
        # Do not add same object over and over
        result = await self.session.execute(select(ShopUnitStatistics).where((ShopUnitStatistics.id == unit.id) &
                                                                             (ShopUnitStatistics.date == unit.date)))
        existing_unit = result.scalars().one_or_none()

        if existing_unit is not None:
            return

        old_values = get_dict_from_unit(unit, unit.date, include_category_price=True)
        statistics_unit = ShopUnitStatistics(**old_values)
        self.session.add(statistics_unit)

    async def update_unit(self, old_unit: ShopUnit, new_values: dict):
        if new_values["type"] != old_unit.type:
            raise HTTPException(status_code=400, message="Validation Failed")

        await self.add_to_statistics(old_unit)

        # Обновить текущий юнит
        for k, v in new_values.items():
            setattr(old_unit, k, v)
        self.session.add(old_unit)

    async def update_ancestors(self, unit: Union[ShopUnit, ShopUnitImport], date: Optional[datetime] = None,
                               price_diff: Optional[float] = None, count_diff: Optional[int] = 0):
        while unit is not None:
            logging.getLogger(__name__).error(f"[{unit.id}] start updating"
                                              f"price diff: {price_diff}. count diff: {count_diff}.")
            if unit.parentId is None:
                break

            # get ancestor
            unit = await get_shop_unit(unit.parentId, self.session, for_update=True)

            if unit is None:
                break

            if date is not None:
                unit.date = date

            if price_diff is not None:
                price = unit.price
                count = unit.children_item_count
                if count + count_diff == 0:
                    unit.price = 0
                else:
                    logging.getLogger(__name__).error(f"[{unit.id}] price before: {unit.price}. count: {count}")
                    unit.price = (price * count + price_diff) / (count + count_diff)
                    logging.getLogger(__name__).error(f"[{unit.id}] price after: {unit.price}")
                unit.children_item_count = count + count_diff

            await self.add_to_statistics(unit)
