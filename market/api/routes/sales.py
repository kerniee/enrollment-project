from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from market.api.db import db
from market.api.schema import UTCdatetime, \
    ShopUnitStatisticResponse
from market.db.schema import ShopUnit, ShopUnitType

router = APIRouter(
    prefix="/sales",
    tags=["Дополнительные задачи"],
)


@router.get("", response_model=ShopUnitStatisticResponse)
async def sales(date: UTCdatetime, session: AsyncSession = Depends(db.get_session)):
    start_date = date - timedelta(days=1)

    stmt = select(ShopUnit).where((ShopUnit.type == ShopUnitType.offer) &
                                  (date >= ShopUnit.date) &
                                  (start_date <= ShopUnit.date))

    result = await session.execute(stmt)
    items = result.scalars().all()

    return {"items": items}
