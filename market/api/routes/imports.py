import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from market.api.crud import UnitCRUD, get_dict_from_unit, get_shop_unit, session_commit
from market.api.db import db
from market.api.schema import ShopUnitImportRequest
from market.db.schema import ShopUnit, ShopUnitType
from market.utils.exceptions import HTTPException

router = APIRouter(
    prefix="/imports",
    tags=["Базовые задачи"],
)


@router.post("")
async def imports(data: ShopUnitImportRequest, session: AsyncSession = Depends(db.get_session)):
    crud = UnitCRUD(session)
    data.items.sort(key=lambda e: e.type.value)

    ids = set()
    for unit in data.items:
        if unit.id in ids:
            raise HTTPException(status_code=400, message="Validation Failed")
        ids.add(unit.id)

        old_unit = await get_shop_unit(unit.id, session, for_update=True)

        if unit.id == unit.parentId:
            raise HTTPException(status_code=400, message="Validation Failed")

        values = get_dict_from_unit(unit, data.updateDate)

        if old_unit is None:
            # Добавить новый юнит
            unit = ShopUnit(**values)
            if unit.price is None:
                unit.price = 0
            if unit.children_item_count is None:
                unit.children_item_count = 0
            session.add(unit)
            await crud.update_ancestors(unit, data.updateDate, unit.price,
                                        count_diff=1 if unit.type == ShopUnitType.offer else 0)
        else:
            # Обновить существующий юнит
            if unit.type == ShopUnitType.category:
                price_diff = None
            else:
                price_diff = unit.price - old_unit.price
                logging.getLogger(__name__).error(f"price diff: {price_diff}")

            parent_id_changed = old_unit.parentId != unit.parentId
            count_diff = old_unit.children_item_count if old_unit.type == ShopUnitType.category else 1
            new_price = old_unit.price * count_diff if old_unit.type == ShopUnitType.category else unit.price

            if parent_id_changed:
                # Новый родитель, пересчитать дату и цену старых родительских юнитов, убрав юнит
                await crud.update_ancestors(old_unit, data.updateDate, -old_unit.price * count_diff,
                                            count_diff=-count_diff)

            await crud.update_unit(old_unit, values)

            if parent_id_changed:
                # Новый родитель, пересчитать дату и цену новых родительских юнитов, добавив юнит
                await crud.update_ancestors(unit, data.updateDate, new_price, count_diff=count_diff)
            else:
                # Родитель не изменился, пересчитываем дату и разницу в цене
                await crud.update_ancestors(unit, data.updateDate, price_diff, count_diff=0)

    await session_commit(session)
