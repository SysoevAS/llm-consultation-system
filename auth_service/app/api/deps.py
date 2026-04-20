from collections.abc import AsyncGenerator

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidTokenError
from app.core.security import decode_token
from app.db.models import User
from app.db.session import AsyncSessionLocal
from app.repositories.users import UsersRepository
from app.usecases.auth import AuthUseCase

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


def get_users_repo(
    db: AsyncSession = Depends(get_db),
) -> UsersRepository:
    return UsersRepository(db)


def get_auth_uc(
    users_repo: UsersRepository = Depends(get_users_repo),
) -> AuthUseCase:
    return AuthUseCase(users_repo)


async def get_current_user_id(
    token: str = Depends(oauth2_scheme),
) -> int:
    payload = decode_token(token)

    sub = payload.get("sub")
    if sub is None:
        raise InvalidTokenError("Token payload does not contain 'sub'")

    try:
        return int(sub)
    except (TypeError, ValueError) as exc:
        raise InvalidTokenError("Token 'sub' must be an integer user id") from exc


async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    auth_uc: AuthUseCase = Depends(get_auth_uc),
) -> User:
    return await auth_uc.me(user_id)