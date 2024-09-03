from datetime import UTC, datetime

from apis.schemas.login import LoginRequest
from apis.schemas.token import Token
from crypto import pwd_context
from crypto.security import create_access_token
from database.exports import SessionDep, User
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


async def authenticate_user(username: str, password: str, db: AsyncSession) -> User | None:
    user = await db.execute(select(User).where((User.username == username) & (User.is_enabled.is_(True))))
    user = user.scalars().first()

    if not user:
        return None
    if not pwd_context.verify(password, user.password_hash):
        return None

    return user


@router.post("/token", response_model=Token)
async def login_for_access_token(db: SessionDep, form_data: LoginRequest):
    user = await authenticate_user(form_data.username, form_data.password, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Incorrect username or password",
        )
    user.last_login = datetime.now(UTC)
    access_token = create_access_token(data={"sub": user.username})

    return {"access_token": access_token, "token_type": "bearer"}
