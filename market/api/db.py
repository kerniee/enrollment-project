from market.utils.pg import DEFAULT_PG_URL
from market.db.base import Database
import os

db_url = os.getenv("MARKET_PG_URL", default=DEFAULT_PG_URL)
db = Database(db_url)
