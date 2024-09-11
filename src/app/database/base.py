import logging
from io import StringIO

from database import sync_engine
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import DeclarativeBase

# https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#sqlalchemy.ext.asyncio.AsyncAttrs
_AsyncBase = type("_AsyncBase", (AsyncAttrs, DeclarativeBase), {})
Base = automap_base(_AsyncBase)

# automap_base() needs a sync engine to autoload metadata currently
# TODO: Reimplement error handling once we know what exceptions are raised on failure
Base.prepare(autoload_with=sync_engine)


# Log the automapped schema to console
def log_schema(model_class):
    # Build up a string message for logging
    with StringIO() as io:
        print("\n" + "-" * 50, file=io)
        print(f"Automapped schema for table {model_class.__name__}", file=io)
        print("-" * 50, file=io)

        mapper = inspect(model_class)
        print("Columns\n-------", file=io)
        for name, column in mapper.columns.items():
            python_type: type = column.type.python_type
            python_typename: str = (
                python_type.__qualname__
                if python_type.__module__ == "builtins"
                else f"{python_type.__module__}.{python_type.__qualname__}"
            )
            print(f"{name}:", repr(column), "->", python_typename, file=io)

        if len(mapper.relationships) > 0:
            print("\nRelationships\n-------------", file=io)
            for r_name, r in mapper.relationships.items():
                local_columns: str = (
                    next(iter(r.local_columns)).name
                    if len(r.local_columns) == 1
                    else str([c.name for c in r.local_columns])
                )
                remote_side: str = (
                    next(iter(r.remote_side)).name
                    if len(r.remote_side) == 1
                    else str([c.name for c in r.remote_side])
                )
                print(
                    f"{r_name}: {model_class.__name__}.{local_columns} -> {r.target.name}.{remote_side}, {r.direction.name}",
                    file=io,
                )
        print("", file=io)
        logging.info(io.getvalue())


# Log the automapped schema of each table
for cls in Base.classes:
    # Exclude Liquibase tables
    if cls.__name__ not in ["databasechangelog", "databasechangeloglock"]:
        log_schema(cls)
