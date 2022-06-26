from collections import defaultdict
from datetime import datetime
from typing import Optional, List, Set
from typing import Union
from uuid import UUID

from sqlalchemy import select, update, bindparam, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from market.api.schema import ShopUnitImport
from market.db.schema import ShopUnit
from market.db.schema import ShopUnitStatistics, ShopUnitType
from market.utils.exceptions import HTTPException


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
    SHOP_UNIT_COLS = (ShopUnit.id, ShopUnit.name, ShopUnit.date, ShopUnit.parentId,
                      ShopUnit.type, ShopUnit.price, ShopUnit.children_count)
    _SHOP_UNIT_COLS_NAMES = tuple(x.key for x in SHOP_UNIT_COLS)
    VALUES_TO_INSERT = dict(id=bindparam("id"), name=bindparam("name"), parentId=bindparam("parentId"),
                            price=bindparam("price"), date=bindparam("date"))
    VALUES_TO_UPDATE = VALUES_TO_INSERT.copy()
    VALUES_TO_UPDATE.pop("id")

    def __init__(self, session: AsyncSession):
        self.session = session
        self.units = dict()
        self.statistics_insert = list()

    @classmethod
    def _get_atr(cls, unit, atr_name):
        if atr_name in UnitCRUD._SHOP_UNIT_COLS_NAMES:
            i = cls._SHOP_UNIT_COLS_NAMES.index(atr_name)
            return unit[i]

    async def _exec_stmt(self, stmt, with_for_update=False):
        if with_for_update:
            result = await self.session.execute(select(stmt).with_for_update())
        else:
            result = await self.session.execute(select(stmt))
        return result.all()

    async def recursive_tree(self, unit_ids: Union[List[UUID], Set[UUID]],
                             columns=SHOP_UNIT_COLS, with_for_update=False):
        beginning_getter = select(columns). \
            filter(ShopUnit.id.in_(unit_ids)).cte(name='children_for', recursive=True)
        with_recursive = beginning_getter.union_all(
            select(columns).filter(ShopUnit.parentId == beginning_getter.c.id).distinct()
        )
        return await self._exec_stmt(with_recursive, with_for_update=with_for_update)

    async def recursive_find_parents(self, unit_ids: Union[List[UUID], Set[UUID]],
                                     columns=SHOP_UNIT_COLS, with_for_update=False):
        beginning_getter = select(columns). \
            filter(ShopUnit.id.in_(unit_ids)).cte(name='parent_for', recursive=True)
        with_recursive = beginning_getter.union_all(
            select(columns).filter(ShopUnit.id == beginning_getter.c.parentId).distinct()
        )
        return await self._exec_stmt(with_recursive, with_for_update=with_for_update)

    # async def update_all_prices_and_dates(self, new_date: Union[datetime, None] = None, skip_ids=None):
    #     stmt = select((ShopUnit.id,)).where(ShopUnit.parentId.is_(None))
    #     root_unit_ids = (await self.session.execute(stmt)).scalars().all()
    #     await self.update_some_prices_and_dates(root_unit_ids, new_date, skip_ids)

    async def delete_and_update_parent_prices(self, chain: List):
        """
        :param chain: result of `recursive_find_parents`, includes unit itself and root node
        """
        if len(chain) == 1:
            return

        price = UnitCRUD._get_atr(chain[0], "price")
        count = UnitCRUD._get_atr(chain[0], "children_count")
        if count <= 0:
            count = 1

        price_diff = -price * count
        count_diff = -count

        update_params = []
        for unit in chain[1:]:
            id_ = UnitCRUD._get_atr(unit, "id")
            avr_price = UnitCRUD._get_atr(unit, "price")
            count = UnitCRUD._get_atr(unit, "children_count")

            if count + count_diff == 0:
                new_price = 0
            else:
                new_price = (avr_price * count + price_diff) / (count + count_diff)
            update_params.append({
                "unit_id": id_,
                "new_price": new_price,
                "new_count": count + count_diff
            })
        stmt = update(ShopUnit).where(ShopUnit.id == bindparam("unit_id"))
        stmt = stmt.values(price=bindparam("new_price"),
                           children_count=bindparam("new_count"))
        await self.session.execute(stmt, update_params)

    async def update_some_prices_and_dates(self, root_ids: Union[List[UUID], Set[UUID]],
                                           new_date: Union[datetime, None] = None,
                                           skip_ids=None):
        if skip_ids is None:
            skip_ids = set()

        units = await self.recursive_tree(root_ids)
        if len(units) < 2:
            return

        map_price = defaultdict(int)
        map_date = {}
        map_avr_price = dict()
        map_num_of_children = defaultdict(int)
        to_update_ids = set()

        for unit in reversed(units):
            id_ = UnitCRUD._get_atr(unit, "id")
            name = UnitCRUD._get_atr(unit, "name")
            parent_id = UnitCRUD._get_atr(unit, "parentId")
            date = UnitCRUD._get_atr(unit, "date")
            type_ = UnitCRUD._get_atr(unit, "type")
            price = UnitCRUD._get_atr(unit, "price")

            map_date[id_] = date

            if type_ == ShopUnitType.category:
                if map_price[id_] == 0:
                    map_avr_price[id_] = 0
                else:
                    map_avr_price[id_] = map_price[id_] / map_num_of_children[id_]
                    map_price[parent_id] += map_price[id_]
                if id_ in skip_ids:
                    to_update_ids.add(parent_id)
                if id_ not in skip_ids and (map_avr_price[id_] != price or id_ in to_update_ids):
                    to_update_ids.add(parent_id)
                    self.statistics_insert.append({
                        "id": id_,
                        "name": name,
                        "parentId": parent_id,
                        "date": date,
                        "type": type_,
                        "price": price
                    })
                    if new_date is not None:
                        map_date[id_] = new_date
            else:
                map_price[parent_id] += price

            count = 1 if map_num_of_children[id_] == 0 else map_num_of_children[id_]
            map_num_of_children[parent_id] += count

        stmt = update(ShopUnit).where(ShopUnit.id == bindparam("unit_id"))
        stmt = stmt.values(price=bindparam("new_price"),
                           date=bindparam("new_date"),
                           children_count=bindparam("count"))
        params = [{"unit_id": id_, "new_price": price,
                   "new_date": map_date[id_], "count": map_num_of_children[id_]}
                  for id_, price in map_avr_price.items()]
        await self.session.execute(stmt, params)

    async def get_shop_unit(self, unit_id, for_update: bool = False) -> Optional[ShopUnit]:
        if unit_id in self.units:
            return self.units[unit_id]

        if for_update:
            result = await self.session.execute(select(ShopUnit).where(ShopUnit.id == unit_id).with_for_update())
        else:
            result = await self.session.execute(select(ShopUnit).where(ShopUnit.id == unit_id))
        unit = result.scalars().one_or_none()
        if unit is not None:
            self.units[unit_id] = unit
        return unit

    def add_to_statistics_insert_batch(self, unit: ShopUnit):
        old_values = get_dict_from_unit(unit, unit.date, include_category_price=True)
        self.statistics_insert.append(old_values)

    async def apply_statistics_insert(self):
        stmt = insert(ShopUnitStatistics).values(UnitCRUD.VALUES_TO_INSERT)
        # self.statistics_insert = list(filter(lambda e: e["id"] not in skip_ids, self.statistics_insert))
        if len(self.statistics_insert) > 0:
            await self.session.execute(stmt, self.statistics_insert)
