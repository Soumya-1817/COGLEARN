from collections.abc import Callable
from uuid import UUID
from fastapi import Depends, HTTPException, Query, WebSocket, WebSocketException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.core.tenant import set_current_tenant_id
from app.models.institution import Institution
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Decodes the RS256 JWT access token, enforces multi-tenant context,
    and loads the authenticated user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id_str: str | None = payload.get("sub")
        tenant_id_str: str | None = payload.get("tenant_id")
        token_type: str | None = payload.get("token_type")

        if user_id_str is None or token_type != "access":
            raise credentials_exception

        user_id = UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    # Establish tenant isolation in the execution context
    if tenant_id_str:
        set_current_tenant_id(tenant_id_str)
    else:
        set_current_tenant_id(None)

    user = await db.get(User, user_id)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive or disabled",
        )

    return user


def require_role(*allowed_roles: UserRole | str) -> Callable:
    """
    Role-Based Access Control (RBAC) dependency factory.
    Enforces that the current authenticated user belongs to one of the specified roles.
    """
    valid_roles = {
        role.value if isinstance(role, UserRole) else str(role) for role in allowed_roles
    }

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role_val = (
            current_user.role.value
            if isinstance(current_user.role, UserRole)
            else str(current_user.role)
        )
        if user_role_val not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of the following roles: {list(valid_roles)}",
            )
        return current_user

    return role_checker


async def get_current_institution(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Institution:
    """
    Retrieves the tenant institution corresponding to the authenticated user.
    """
    if current_user.institution_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user has no associated institution tenant.",
        )

    institution = await db.get(Institution, current_user.institution_id)
    if institution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant institution not found.",
        )
    if not institution.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant institution is currently deactivated.",
        )

    return institution


async def get_current_user_ws(
    websocket: WebSocket,
    token: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Authenticates WebSocket connections using JWT token from query parameter or authorization header.
    """
    raw_token = token
    if not raw_token:
        # Check query params directly from scope
        raw_token = websocket.query_params.get("token")
    if not raw_token:
        auth_hdr = websocket.headers.get("authorization")
        if auth_hdr and auth_hdr.startswith("Bearer "):
            raw_token = auth_hdr[7:]

    if not raw_token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Missing authentication token")

    try:
        payload = decode_token(raw_token)
        user_id_str: str | None = payload.get("sub")
        tenant_id_str: str | None = payload.get("tenant_id")
        token_type: str | None = payload.get("token_type")

        if user_id_str is None or token_type != "access":
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token claims")

        user_id = UUID(user_id_str)
    except (JWTError, ValueError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Could not validate token")

    if tenant_id_str:
        set_current_tenant_id(tenant_id_str)
    else:
        set_current_tenant_id(None)

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="User not active or not found")

    return user
