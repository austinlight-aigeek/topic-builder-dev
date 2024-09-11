from datetime import UTC, datetime, timedelta
from os import environ
from typing import Annotated
from uuid import uuid4

from database.exports import SessionDep, User
from fastapi import Depends, Request
from jose import jwt
from sqlalchemy import select

ACCESS_TOKEN_EXPIRE_MINUTES = 60  # in mins
ALGORITHM = "HS256"
SECRET_KEY = environ["JWT_KEY"]  # Fail loudly if no JWT key is provided


# Exception class for handling requests with no token
class UnauthorizedError(Exception):
    pass


# Exception class when token is valid but user could not be found (empty/invalid)
class UserNotFoundError(Exception):
    pass


# Exception class when user is not allowed to perform this type of operation
class ForbiddenError(Exception):
    pass


### Token validation ###


# Access token, submitted as cookie for UI, header for API
def create_access_token(
    data: dict,
    expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
):
    expires = datetime.now(UTC) + expires_delta
    access_token_id = str(uuid4())
    return jwt.encode(
        data | {"exp": expires, "jti": access_token_id}, SECRET_KEY, ALGORITHM
    )


def validate_access_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


### User validation ###


async def get_user(request: Request, db: SessionDep):
    if request.url.path.startswith("/api"):
        value = request.headers.get("Authorization", "")
        scheme, _, token_str = value.partition(" ")
        if scheme.lower() != "bearer":
            raise UnauthorizedError
    else:
        token_str = request.cookies.get("access_token")

    if token_str is None:
        raise UnauthorizedError
    token = validate_access_token(token_str)

    username = token.get("sub", "")
    result_set = await db.execute(
        select(User).where((User.username == username) & (User.is_enabled.is_(True)))
    )
    user = result_set.scalars().first()  # Will be None if no user is found

    if user is None:
        raise UserNotFoundError
    return user


UserDep = Annotated[User, Depends(get_user)]


async def get_superuser(user: UserDep):
    if not user.is_superuser:
        raise ForbiddenError
    return user


SuperuserDep = Annotated[User, Depends(get_superuser)]
