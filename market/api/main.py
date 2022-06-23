import logging
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from pydantic.json import ENCODERS_BY_TYPE
from sqlalchemy.exc import IntegrityError

from market.api.routes import ROUTERS
from market.utils.argparse import clear_environ
from market.utils.date import convert_datetime_to_iso_8601_with_z_suffix
from market.utils.exceptions import HTTPException

ENCODERS_BY_TYPE[datetime] = lambda date_obj: convert_datetime_to_iso_8601_with_z_suffix(date_obj)

app = FastAPI()
logger = logging.getLogger(__name__)

APP_PREFIX = "MARKET_"
clear_environ(lambda e: e.startswith(APP_PREFIX))

for router in ROUTERS:
    app.include_router(router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.message},
    )


@app.exception_handler(RequestValidationError)
@app.exception_handler(IntegrityError)
async def pydantic_exception_handler(request: Request, exc: ValidationError):
    logger.warning(str(exc))
    return JSONResponse(
        status_code=400,
        content={"code": 400, "message": "Validation Failed"},
    )
