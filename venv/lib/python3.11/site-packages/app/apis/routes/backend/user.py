from uuid import UUID, uuid4

from apis.schemas.user import ShowUser, UserCreate, UserUpdate
from crypto import pwd_context
from crypto.security import SuperuserDep
from database.exports import SessionDep, User
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import delete, select, update

router = APIRouter()


@router.post("/", response_model=ShowUser, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: SessionDep, superuser: SuperuserDep):  # noqa: ARG001. Depends arg used for auth
    user = User(
        id=uuid4(),
        username=user.username,
        password_hash=pwd_context.hash(user.password),
        is_enabled=user.is_enabled,
        is_superuser=user.is_superuser,
    )
    db.add(user)

    return user


@router.get("/{id_}", response_model=ShowUser)
async def get_user(id_: UUID, db: SessionDep, superuser: SuperuserDep):  # noqa: ARG001. Depends arg used for auth
    user = await db.execute(select(User).filter(User.id == id_))
    user = user.scalars().first()
    if not user:
        raise HTTPException(detail=f"user with ID {id_} does not exist.", status_code=status.HTTP_404_NOT_FOUND)

    return user


@router.get("", response_model=list[ShowUser])
async def get_all_users(db: SessionDep, superuser: SuperuserDep):  # noqa: ARG001. Depends arg used for auth
    users = await db.execute(select(User))
    return users.scalars().all()


@router.put("/{id_}")
async def update_user(id_: UUID, user_update: UserUpdate, db: SessionDep, superuser: SuperuserDep):  # noqa: ARG001. Depends arg used for auth
    result = await db.execute(
        update(User)
        .where(User.id == id_)
        .values(
            username=user_update.username,
            password_hash=pwd_context.hash(user_update.password),
            is_enabled=user_update.is_enabled,
            is_superuser=user_update.is_superuser,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(detail=f"User with ID {id_} does not exist.", status_code=status.HTTP_404_NOT_FOUND)


@router.delete("/{id_}")
async def delete_user(id_: UUID, db: SessionDep, superuser: SuperuserDep):  # noqa: ARG001. Depends arg used for auth
    result = await db.execute(delete(User).where(User.id == id_))
    if result.rowcount == 0:
        raise HTTPException(detail=f"User with ID {id_} does not exist.", status_code=status.HTTP_404_NOT_FOUND)
