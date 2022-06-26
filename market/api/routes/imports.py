from fastapi import APIRouter, Depends
from sqlalchemy import select, bindparam, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from market.api.crud import UnitCRUD, get_dict_from_unit, session_commit
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
    if len(data.items) == 0:
        return

    crud = UnitCRUD(session)
    data.items.sort(key=lambda e: e.type.value)

    # get ids, check constraints
    ids = set()
    parent_ids = set()
    root_ids = set()
    for unit in data.items:
        if unit.parentId is None:
            root_ids.add(unit.id)
        if unit.id in ids or unit.id == unit.parentId:
            # uuid товара или категории является уникальным среди товаров и категорий
            # дополнение: юнит не может быть родителем самого себя
            raise HTTPException(status_code=400, message="Validation Failed")
        ids.add(unit.id)
        parent_ids.add(unit.parentId)

    # lock trees for update
    parents = await crud.recursive_find_parents(ids.union(parent_ids))
    for parent in parents:
        if parent[3] is None:  # parent[3] == parentId
            root_ids.add(parent[0])  # parent[0] == id
    await crud.recursive_tree(root_ids, with_for_update=True)

    # get existing units (which will be updated in this import)
    existing_units = await session.execute(select(ShopUnit).where(ShopUnit.id.in_(ids)))
    existing_units = existing_units.scalars().all()
    existing_unit_ids_type = {unit.id: unit.type for unit in existing_units}
    del ids

    # mark items to update and insert, check constraints
    upserted_ids = set()
    upsert_params = []
    update_parent_params = []
    for unit in data.items:
        if unit.id in existing_unit_ids_type and existing_unit_ids_type[unit.id] != unit.type:
            # Изменение типа элемента с товара на категорию или с категории на товар не допускается
            raise HTTPException(status_code=400, message="Validation Failed")
        # if unit.id not in existing_unit_ids_type:
        upserted_ids.add(unit.id)

        values = get_dict_from_unit(unit, data.updateDate, include_category_price=True)
        if values["price"] is None:
            values["price"] = 0
        update_parent_values = {"unit_id": values["id"], "parentId": values["parentId"]}

        del values["parentId"]
        upsert_params.append(values)
        update_parent_params.append(update_parent_values)

    # add updated units to statistics before their update
    for unit in existing_units:
        crud.add_to_statistics_insert_batch(unit)

    # insert and update all imported units
    insert_values = UnitCRUD.VALUES_TO_INSERT.copy()
    insert_values.pop("parentId")
    update_values = UnitCRUD.VALUES_TO_UPDATE.copy()
    update_values.pop("parentId")

    upsert_stmt = insert(ShopUnit).values(insert_values)
    upsert_stmt = upsert_stmt.on_conflict_do_update(index_elements=["id"], set_=update_values)
    await session.execute(upsert_stmt, upsert_params)

    # insert and update parents
    update_stmt = update(ShopUnit).where(ShopUnit.id == bindparam("unit_id")).values(parentId=bindparam("parentId"))
    await session.execute(update_stmt, update_parent_params)
    del upsert_params

    # check task constraint
    parent_ids_stmt = select(ShopUnit.parentId).where(ShopUnit.parentId.is_not(None)).distinct()
    if len(parent_ids) > 0:
        stmt = select(ShopUnit).where((ShopUnit.id.in_(parent_ids_stmt)) & (ShopUnit.type == ShopUnitType.offer))
        wrong_units = (await session.execute(stmt)).scalars().all()
        if len(wrong_units) != 0:
            # родителем товара или категории может быть только категория
            await session.rollback()
            raise HTTPException(status_code=400, message="Validation Failed")

    # await crud.update_all_prices_and_dates(data.updateDate, added_unit_ids)
    await crud.update_some_prices_and_dates(root_ids, data.updateDate, upserted_ids)
    await crud.apply_statistics_insert()
    await session_commit(session)

    # for unit in data.items:
    #     old_unit = await crud.get_shop_unit(unit.id, for_update=True)
    #
    #     values = get_dict_from_unit(unit, data.updateDate)
    #
    #     if unit.id in new_units:
    #         # Это новый юнит, добавить parentId и обновить предков
    #         new_unit = new_units[unit.id]
    #         new_unit.parentId = unit.parentId
    #         await crud.update_ancestors(new_unit, data.updateDate, new_unit.price,
    #                                     count_diff=1 if new_unit.type == ShopUnitType.offer else 0)
    #     else:
    #         # Обновить существующий юнит
    #         if unit.type == ShopUnitType.category:
    #             price_diff = None
    #         else:
    #             price_diff = unit.price - old_unit.price
    #             # logging.getLogger(__name__).error(f"price diff: {price_diff}")
    #
    #         parent_id_changed = old_unit.parentId != unit.parentId
    #         count_diff = old_unit.children_item_count if old_unit.type == ShopUnitType.category else 1
    #         new_price = old_unit.price * count_diff if old_unit.type == ShopUnitType.category else unit.price
    #
    #         if parent_id_changed:
    #             # Новый родитель, пересчитать дату и цену старых родительских юнитов, убрав юнит
    #             await crud.update_ancestors(old_unit, data.updateDate, -old_unit.price * count_diff,
    #                                         count_diff=-count_diff)
    #
    #         await crud.update_unit(old_unit, values)
    #
    #         if parent_id_changed:
    #             # Новый родитель, пересчитать дату и цену новых родительских юнитов, добавив юнит
    #             await crud.update_ancestors(unit, data.updateDate, new_price, count_diff=count_diff)
    #         else:
    #             # Родитель не изменился, пересчитываем дату и разницу в цене
    #             await crud.update_ancestors(unit, data.updateDate, price_diff, count_diff=0)
    #
    # await session_commit(session)
