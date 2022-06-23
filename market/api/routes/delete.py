from fastapi import APIRouter, Depends
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from market.api.crud import get_shop_unit, UnitCRUD, session_commit
from market.api.db import db
from market.utils.exceptions import HTTPException

router = APIRouter(
    prefix="/delete",
    tags=["Базовые задачи"],
)


@router.delete("/{unit_id}")
async def delete_unit(unit_id: UUID4, session: AsyncSession = Depends(db.get_session)):
    crud = UnitCRUD(session)
    unit = await get_shop_unit(unit_id, session, for_update=True)
    if unit is None:
        raise HTTPException(404, "Item not found")
    await crud.update_ancestors(unit, price_diff=-unit.price, count_diff=-1)
    await session.delete(unit)
    await session_commit(session)
