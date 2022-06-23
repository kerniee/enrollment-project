FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

ENV MODULE_NAME=api.main

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./prestart.sh /app/prestart.sh

ENV PYTHONPATH=/app/market
COPY ./market /app/market