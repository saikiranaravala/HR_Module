from alembic import context
from sqlalchemy import create_engine

from platform_core.db import database_url


def run_migrations_online() -> None:
    engine = create_engine(database_url(), future=True)
    with engine.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


run_migrations_online()
