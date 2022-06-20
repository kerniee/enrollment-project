"""
Утилита для управления состоянием базы данных, обертка над alembic.
Можно вызывать из любой директории, а также указать произвольный DSN для базы
данных, отличный от указанного в файле alembic.ini.
"""
import argparse
import logging

from alembic.config import CommandLine
from decouple import config

from market.utils.pg import DEFAULT_PG_URL, make_alembic_config


def main():
    logging.basicConfig(level=logging.DEBUG)

    alembic = CommandLine()
    alembic.parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter
    alembic.parser.add_argument(
        '--pg-url', default=config('MARKET_PG_URL', default=DEFAULT_PG_URL),
        help='Database URL [env var: MARKET_PG_URL]'
    )

    options = alembic.parser.parse_args()
    if 'cmd' not in options:
        alembic.parser.error('too few arguments')
        exit(128)
    else:
        alembic_config = make_alembic_config(options)
        exit(alembic.run_cmd(alembic_config, options))


if __name__ == '__main__':
    main()
