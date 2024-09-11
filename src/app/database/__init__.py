from os import environ

import numpy as np
from pgvector.psycopg import register_vector, register_vector_async
from pgvector.sqlalchemy import (
    Vector,
)  # Import loads `vector` type handler into SQLAlchemy
from sqlalchemy import URL, create_engine, event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

Vector.python_type = np.ndarray  # Prevent NotImplementedError when we log schema

# Use URL so we don't need to escape special characters
sa_url = URL.create(
    "postgresql+psycopg",
    environ.get("POSTGRES_USER", "postgres"),
    environ.get("POSTGRES_PASSWORD", "postgres"),
    environ.get("POSTGRES_HOST", "localhost"),
    int(environ.get("POSTGRES_PORT", 5432)),
    environ.get("POSTGRES_DBNAME"),
)

engine = create_async_engine(sa_url)
sync_engine = create_engine(sa_url)


# Register vector on new connections to support vector parameters
# https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#using-events-with-the-asyncio-extension
@event.listens_for(engine.sync_engine, "connect")
def register_vector_async_on_connect(
    dbapi_connection, connection_record
):  # noqa: ARG001. Argument needed for compatibility
    dbapi_connection.run_async(register_vector_async)


@event.listens_for(sync_engine, "connect")
def register_vector_on_connect(
    dbapi_connection, connection_record
):  # noqa: ARG001. Argument needed for compatibility
    register_vector(dbapi_connection)


AsyncSessionmaker = async_sessionmaker(engine, expire_on_commit=False)
