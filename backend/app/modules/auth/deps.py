from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.modules.auth.models import AdminUser
from app.modules.auth.service import InvalidTokenError, decode_access_token

bearer = HTTPBearer(auto_error=False, description="Token obtido em /api/v1/auth/verify")

UNAUTHORIZED = HTTPException(
    status.HTTP_401_UNAUTHORIZED,
    detail="Não autenticado",
    headers={"WWW-Authenticate": "Bearer"},
)


async def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: AsyncSession = Depends(get_session),
) -> AdminUser:
    if credentials is None:
        raise UNAUTHORIZED
    try:
        admin_id = decode_access_token(credentials.credentials)
    except InvalidTokenError:
        raise UNAUTHORIZED from None
    admin = await session.get(AdminUser, admin_id)
    if admin is None or not admin.is_active:
        raise UNAUTHORIZED
    return admin
