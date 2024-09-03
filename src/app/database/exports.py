from typing import Annotated

from database import AsyncSessionmaker
from database.base import Base  # Import automaps and logs SQLAlchemy schema
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.decl_api import DeclarativeMeta

# Extract SQLAlchemy models from Automap Base
User: DeclarativeMeta = Base.classes.user_
Ruleset: DeclarativeMeta = Base.classes.ruleset
Sentence: DeclarativeMeta = Base.classes.sentence


async def async_session():
    async with AsyncSessionmaker.begin() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(async_session)]
