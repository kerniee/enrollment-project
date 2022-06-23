REST API сервис для веб-сервиса сравнения цен.
Вступительное задание в Летнюю Школу Бэкенд Разработки Яндекса 2022.

## Что внутри?

Приложение упаковано в Docker-контейнер и разворачивается с помощью Ansible.  
Внутри Docker-контейнера доступен python модуль `market.db` — утилита для управления состоянием базы данных.

## Как использовать?

Как запустить REST API сервис локально на порту 80:  
(миграции автоматически применяются при запуске)

```shell
docker run -it -p 80:80 \
    -e MARKET_PG_URL=postgresql+asyncpg://user:hackme@localhost/market \
    kernie/backendschool2022
```

Все доступные опции запуска утилиты `market.db` можно получить при помощи команды `--help`:

```shell
docker run kernie/backendschool2022 python -m market.db --help
```

# Разработка

## Быстрые команды

- `make` Отобразить список доступных команд

## Как подготовить окружение для разработки?

```shell
make devenv
make postgres
source env/bin/activate
python -m market.db upgrade head
uvicorn market.api.main:app --port 80 --host 0.0.0.0
```

## Как запустить тесты локально?

```shell
make devenv
make postgres
source env/bin/activate
python -m market.db upgrade head
uvicorn market.api.main:app --port 80 --host 0.0.0.0
make test
```