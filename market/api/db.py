import os

from market.db.base import Database
from market.utils.pg import DEFAULT_PG_URL

db_url = os.getenv("MARKET_PG_URL", default=DEFAULT_PG_URL)

APP_PREFIX = "MARKET_"
DEBUG = bool(int(os.getenv(APP_PREFIX + "DEBUG", default=0)))

db = Database(db_url, echo=DEBUG)
