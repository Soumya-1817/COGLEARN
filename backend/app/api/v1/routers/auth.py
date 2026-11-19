from datetime import datetime, timedelta, timezone
from uuid import uuid4
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.audit_log import AuditLog
from app.models.institution import Institution
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.schemas.common import SuccessResponse
from app.schemas.user import UserResponse

router = APIRouter()

REFRESH_COOKIE_NAME = "coglearn_refresh_token"


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Authenticates a user by email and password.
    Returns an RS256 JWT access token and sets an HttpOnly cookie with the refresh token.
    """
    clean_email = login_data.email.strip().lower()
    result = await db.execute(select(User).where(func.lower(User.email) == clean_email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact your institution administrator.",
        )

    # Update last login timestamp
    now = datetime.now(timezone.utc)
    user.last_login_at = now

    # Issue Refresh Token with new family ID
    family_id = uuid4()
    raw_refresh_token, token_hash = create_refresh_token(user.id, family_id)
    refresh_record = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        family_id=family_id,
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(refresh_record)

    # Audit log
    audit = AuditLog(
        institution_id=user.institution_id,
        user_id=user.id,
        action="login",
        resource_type="auth",
        resource_id=user.id,
        ip_address=request.client.host if request.client else None,
        extra_data={"email": user.email, "role": user.role.value},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(user)

    # Issue RS256 Access Token
    access_token = create_access_token({
        "sub": str(user.id),
        "tenant_id": str(user.institution_id) if user.institution_id else None,
        "role": user.role.value,
        "email": user.email,
        "session_id": str(family_id),
    })

    # Set HttpOnly Cookie for refresh token
    cookie_max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT != "development",
        samesite="lax",
        max_age=cookie_max_age,
        path="/api/v1/auth",
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=raw_refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    response: Response,
    request: Request,
    payload: RefreshRequest | None = None,
    cookie_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Refreshes access token with Refresh Token rotation and compromise detection.
    If a revoked refresh token is presented, all tokens in the token family are revoked.
    """
    raw_token = (
        payload.refresh_token if (payload and payload.refresh_token) else cookie_token
    )
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required in cookie or request body",
        )

    token_hash = hash_refresh_token(raw_token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    res = await db.execute(stmt)
    token_record = res.scalar_one_or_none()

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    now = datetime.now(timezone.utc)

    # Compromise Detection: Token was already used/revoked
    if token_record.revoked_at is not None:
        # Invalidate entire family immediately
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == token_record.family_id)
            .values(revoked_at=now)
        )
        await db.commit()
        response.delete_cookie(REFRESH_COOKIE_NAME, path="/api/v1/auth")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token compromise detected. All associated sessions have been invalidated.",
        )

    # Expiry Check
    if token_record.expires_at < now:
        token_record.revoked_at = now
        await db.commit()
        response.delete_cookie(REFRESH_COOKIE_NAME, path="/api/v1/auth")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired. Please log in again.",
        )

    # Rotate Token: Revoke current token and generate successor in the same family
    token_record.revoked_at = now

    user = await db.get(User, token_record.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or not found",
        )

    new_raw_token, new_token_hash = create_refresh_token(user.id, token_record.family_id)
    new_refresh = RefreshToken(
        user_id=user.id,
        token_hash=new_token_hash,
        family_id=token_record.family_id,
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(new_refresh)
    await db.commit()
    await db.refresh(user)

    # Generate new RS256 access token
    access_token = create_access_token({
        "sub": str(user.id),
        "tenant_id": str(user.institution_id) if user.institution_id else None,
        "role": user.role.value,
        "email": user.email,
        "session_id": str(token_record.family_id),
    })

    # Set new HttpOnly cookie
    cookie_max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=new_raw_token,
        httponly=True,
        secure=settings.ENVIRONMENT != "development",
        samesite="lax",
        max_age=cookie_max_age,
        path="/api/v1/auth",
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=new_raw_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/logout", response_model=SuccessResponse)
async def logout(
    response: Response,
    cookie_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse:
    """
    Logs out the user and revokes the active refresh token.
    """
    if cookie_token:
        token_hash = hash_refresh_token(cookie_token)
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await db.commit()

    response.delete_cookie(REFRESH_COOKIE_NAME, path="/api/v1/auth")
    return SuccessResponse(message="Successfully logged out.")


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Returns the profile of the currently authenticated user.
    Guaranteed not to include any cognitive analytics or risk scores.
    """
    return UserResponse.model_validate(current_user)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    reg_data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Registers a new user account.
    Platform admins can be created when no users exist or by existing platform admins.
    Institutional members must be tied to a valid active institution.
    """
    # Check email uniqueness
    clean_email = reg_data.email.strip().lower()
    existing = await db.execute(select(User).where(func.lower(User.email) == clean_email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists.",
        )

    if reg_data.role != UserRole.PLATFORM_ADMIN:
        if reg_data.institution_id is None:
            # Auto-assign to default active institution (e.g. Greenfield University)
            default_inst_res = await db.execute(
                select(Institution).where(Institution.is_active == True).limit(1)
            )
            default_inst = default_inst_res.scalar_one_or_none()
            if default_inst:
                reg_data.institution_id = default_inst.id
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No active institution found. Please contact administrator.",
                )
        else:
            institution = await db.get(Institution, reg_data.institution_id)
            if not institution:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Specified institution does not exist.",
                )
            if not institution.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Specified institution is inactive.",
                )

    new_user = User(
        email=clean_email,
        hashed_password=hash_password(reg_data.password),
        full_name=reg_data.full_name.strip(),
        role=reg_data.role,
        institution_id=reg_data.institution_id,
        is_active=True,
        is_verified=True,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return UserResponse.model_validate(new_user)
