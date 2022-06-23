from fastapi import APIRouter, Depends
from pydantic import UUID4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from market.api.db import db
from market.api.schema import UTCdatetime, ShopUnitStatisticResponse
from market.db.schema import ShopUnit, ShopUnitStatistics
from market.utils.exceptions import HTTPException

router = APIRouter(
    prefix="/node",
    tags=["Дополнительные задачи"],
)


@router.get("/{unit_id}/statistic", response_model=ShopUnitStatisticResponse)
async def statistics(unit_id: UUID4, dateStart: UTCdatetime, dateEnd: UTCdatetime,
                     session: AsyncSession = Depends(db.get_session)):
    date_start = dateStart
    date_end = dateEnd

    stmt = select(ShopUnit).where((ShopUnit.id == unit_id) &
                                  (date_end > ShopUnit.date) &
                                  (date_start <= ShopUnit.date))

    result = await session.execute(stmt)
    items = result.scalars().all()

    stmt = select(ShopUnitStatistics).where((ShopUnitStatistics.id == unit_id) &
                                            (date_end > ShopUnitStatistics.date) &
                                            (date_start <= ShopUnitStatistics.date))

    result = await session.execute(stmt)
    items_statistics = result.scalars().all()

    items.extend(items_statistics)

    if len(items) == 0:
        raise HTTPException(404, "Item not found")

    items.sort(key=lambda e: e.id)

    return {"items": items}
