import csv
import io
import secrets
from uuid import UUID
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserBulkImportResult, UserCreate, UserResponse, UserUpdate

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[UserResponse],
    dependencies=[Depends(require_role(UserRole.PLATFORM_ADMIN, UserRole.INST_ADMIN))],
)
async def list_users(
    institution_id: UUID | None = Query(default=None),
    role: UserRole | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[UserResponse]:
    """
    Lists users within the tenant institution.
    Platform admins may filter across any institution.
    """
    offset = (page - 1) * page_size
    query = select(User)

    if current_user.role != UserRole.PLATFORM_ADMIN:
        query = query.where(User.institution_id == current_user.institution_id)
    elif institution_id:
        query = query.where(User.institution_id == institution_id)

    if role:
        query = query.where(User.role == role)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(count_query)
    total = total_res.scalar_one()

    # Paginate
    paged_query = query.order_by(User.created_at.desc()).offset(offset).limit(page_size)
    users_res = await db.execute(paged_query)
    users = users_res.scalars().all()

    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaginatedResponse[UserResponse](
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.PLATFORM_ADMIN, UserRole.INST_ADMIN))],
)
async def create_user(
    data: UserCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Creates a user within the institution tenant."""
    # Check if creating platform admin
    if data.role == UserRole.PLATFORM_ADMIN and current_user.role != UserRole.PLATFORM_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only platform administrators can create other platform administrators.",
        )

    # Determine tenant
    target_institution_id = current_user.institution_id
    if current_user.role == UserRole.PLATFORM_ADMIN:
        target_institution_id = data.institution_id

    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists.",
        )

    new_user = User(
        institution_id=target_institution_id,
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
        is_active=data.is_active,
        is_verified=data.is_verified,
        profile_data=data.profile_data,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return UserResponse.model_validate(new_user)


@router.post(
    "/import-csv",
    response_model=UserBulkImportResult,
    dependencies=[Depends(require_role(UserRole.PLATFORM_ADMIN, UserRole.INST_ADMIN))],
)
async def import_users_csv(
    file: UploadFile = File(...),
    institution_id: UUID | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserBulkImportResult:
    """
    Bulk imports users (e.g., student cohorts) from a CSV file.
    Expected CSV columns: email, full_name, role (optional, defaults to student), password (optional).
    """
    target_institution_id = current_user.institution_id
    if current_user.role == UserRole.PLATFORM_ADMIN:
        if not institution_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Platform admin must provide institution_id query parameter for CSV import.",
            )
        target_institution_id = institution_id

    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a CSV file (.csv)",
        )

    content = await file.read()
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file must be UTF-8 encoded.",
        )

    reader = csv.DictReader(io.StringIO(decoded))
    created_count = 0
    failed_count = 0
    errors: list[str] = []
    row_idx = 1

    for row in reader:
        row_idx += 1
        email = row.get("email", "").strip().lower()
        full_name = row.get("full_name", "").strip()
        role_str = row.get("role", "student").strip().lower()
        raw_password = row.get("password", "").strip() or secrets.token_urlsafe(12)

        if not email or "@" not in email:
            failed_count += 1
            errors.append(f"Row {row_idx}: Invalid or missing email '{email}'")
            continue

        if not full_name:
            failed_count += 1
            errors.append(f"Row {row_idx}: Missing full_name")
            continue

        try:
            user_role = UserRole(role_str)
        except ValueError:
            failed_count += 1
            errors.append(f"Row {row_idx}: Invalid role '{role_str}'")
            continue

        # Prevent elevating to platform_admin through bulk CSV
        if user_role == UserRole.PLATFORM_ADMIN and current_user.role != UserRole.PLATFORM_ADMIN:
            failed_count += 1
            errors.append(f"Row {row_idx}: Cannot create platform_admin via CSV")
            continue

        # Check existing
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            failed_count += 1
            errors.append(f"Row {row_idx}: User with email '{email}' already exists")
            continue

        user = User(
            institution_id=target_institution_id,
            email=email,
            full_name=full_name,
            role=user_role,
            hashed_password=hash_password(raw_password),
            is_active=True,
            is_verified=True,
            profile_data={"initial_password_generated": row.get("password") is None},
        )
        db.add(user)
        created_count += 1

    if created_count > 0:
        await db.commit()

    return UserBulkImportResult(
        total_records=created_count + failed_count,
        created_count=created_count,
        failed_count=failed_count,
        errors=errors[:50],  # Return up to 50 error messages
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Retrieves user details by user ID (Self, Institution Admin, or Platform Admin)."""
    is_self = current_user.id == user_id
    is_platform_admin = current_user.role == UserRole.PLATFORM_ADMIN
    is_inst_admin = current_user.role == UserRole.INST_ADMIN

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if not is_self and not is_platform_admin:
        if not is_inst_admin or user.institution_id != current_user.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this user's profile.",
            )

    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Updates user information."""
    is_self = current_user.id == user_id
    is_platform_admin = current_user.role == UserRole.PLATFORM_ADMIN
    is_inst_admin = current_user.role == UserRole.INST_ADMIN

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if not is_self and not is_platform_admin:
        if not is_inst_admin or user.institution_id != current_user.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this user.",
            )

    update_dict = data.model_dump(exclude_unset=True)

    # Password update
    if "password" in update_dict and update_dict["password"]:
        user.hashed_password = hash_password(update_dict.pop("password"))

    # Role update restricted to admins
    if "role" in update_dict:
        if not (is_platform_admin or is_inst_admin):
            update_dict.pop("role")

    # Activation restricted to admins
    if "is_active" in update_dict:
        if not (is_platform_admin or is_inst_admin):
            update_dict.pop("is_active")

    for field, val in update_dict.items():
        setattr(user, field, val)

    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)
