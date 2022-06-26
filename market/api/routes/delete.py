from fastapi import APIRouter, Depends
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from market.api.crud import UnitCRUD, session_commit
from market.api.db import db
from market.utils.exceptions import HTTPException

router = APIRouter(
    prefix="/delete",
    tags=["Базовые задачи"],
)


@router.delete("/{unit_id}")
async def delete_unit(unit_id: UUID4, session: AsyncSession = Depends(db.get_session)):
    crud = UnitCRUD(session)
    chain = await crud.recursive_find_parents([unit_id], with_for_update=True)
    if len(chain) == 0:
        raise HTTPException(404, "Item not found")

    unit = await crud.get_shop_unit(unit_id)
    await crud.delete_and_update_parent_prices(chain)
    await session.delete(unit)
    await session_commit(session)
