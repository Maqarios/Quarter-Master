"""
Alembic environment configuration for Quarter Master Bot.

This module configures Alembic migrations for both offline and online modes,
with support for autogeneration and type comparison.
"""

from logging.config import fileConfig

from alembic import context
from config import settings

# Import database components (absolute imports from Bot package)
from db.database import Base

# Import all models for autogenerate to detect them
from db.models.api_key import APIKey  # noqa: F401
from db.models.session_token import SessionToken  # noqa: F401
from sqlalchemy import engine_from_config, pool

# Add more model imports here as you create them:
# from db.models.user import User
# from db.models.transaction import Transaction

# Alembic Config object
config = context.config

# Set database URL from settings
config.set_main_option("sqlalchemy.url", settings.database_url)

# Configure logging if config file exists
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine
    creation we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate
    a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_schemas=True,
            render_as_batch=True,  # For SQLite compatibility if needed
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
