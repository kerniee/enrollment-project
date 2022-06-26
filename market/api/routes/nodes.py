from collections import defaultdict
from math import floor
from typing import Union

from fastapi import APIRouter, Depends
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from market.api.crud import UnitCRUD
from market.api.db import db
from market.api.schema import ShopUnitCategory, ShopUnitItem
from market.db.schema import ShopUnitType
from market.utils.exceptions import HTTPException

router = APIRouter(
    prefix="/nodes",
    tags=["Базовые задачи"],
)


def to_pydantic(_unit):
    common = {
        "id": _unit[0],
        "name": _unit[1],
        "date": _unit[2],
        "parentId": _unit[3],
        "type": _unit[4],
        "price": floor(_unit[5]) if _unit[5] is not None else 0
    }
    if _unit[4] == ShopUnitType.category:
        return ShopUnitCategory(**common, children=[])
    if _unit[4] == ShopUnitType.offer:
        return ShopUnitItem(**common, children=None)


@router.get("/{unit_id}", response_model=Union[ShopUnitCategory, ShopUnitItem])
async def node_info(unit_id: UUID4, session: AsyncSession = Depends(db.get_session)):
    crud = UnitCRUD(session)
    units = await crud.recursive_tree([unit_id])

    if len(units) == 0:
        raise HTTPException(404, "Item not found")

    map_children = defaultdict(list)
    root = to_pydantic(units[0])
    if root.type == ShopUnitType.category:
        root.children = map_children[root.id]

    for unit in reversed(units[1:]):
        pydantic_schema = to_pydantic(unit)
        if pydantic_schema.parentId is not None:
            map_children[pydantic_schema.parentId].append(pydantic_schema)

        if pydantic_schema.type == ShopUnitType.category:
            pydantic_schema.children = map_children[pydantic_schema.id]

    return root
