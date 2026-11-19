from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.models.institution import Institution
from app.models.user import User, UserRole
from app.schemas.common import PaginatedResponse
from app.schemas.institution import InstitutionCreate, InstitutionResponse, InstitutionUpdate

router = APIRouter()


@router.post(
    "",
    response_model=InstitutionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.PLATFORM_ADMIN))],
)
async def create_institution(
    data: InstitutionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InstitutionResponse:
    """Creates a new educational institution (Platform Admin only)."""
    existing = await db.execute(select(Institution).where(Institution.slug == data.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Institution slug '{data.slug}' is already registered.",
        )

    inst = Institution(
        name=data.name,
        slug=data.slug,
        domain=data.domain,
        is_demo=data.is_demo,
        is_active=data.is_active,
        settings=data.settings,
    )
    db.add(inst)
    await db.commit()
    await db.refresh(inst)
    return InstitutionResponse.model_validate(inst)


@router.get("/public", response_model=list[dict])
async def list_public_institutions(
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Lists active institutions for public user registration (no auth required)."""
    stmt = select(Institution).where(Institution.is_active == True).order_by(Institution.name)
    res = await db.execute(stmt)
    institutions = res.scalars().all()
    return [
        {"id": str(i.id), "name": i.name, "slug": i.slug, "is_demo": i.is_demo}
        for i in institutions
    ]


@router.get(
    "",
    response_model=PaginatedResponse[InstitutionResponse],
    dependencies=[Depends(require_role(UserRole.PLATFORM_ADMIN))],
)
async def list_institutions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[InstitutionResponse]:
    """Lists all institutions in the platform (Platform Admin only)."""
    offset = (page - 1) * page_size

    total_stmt = select(func.count(Institution.id))
    total_res = await db.execute(total_stmt)
    total = total_res.scalar_one()

    stmt = select(Institution).order_by(Institution.name).offset(offset).limit(page_size)
    res = await db.execute(stmt)
    institutions = res.scalars().all()

    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaginatedResponse[InstitutionResponse](
        items=[InstitutionResponse.model_validate(i) for i in institutions],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{institution_id}", response_model=InstitutionResponse)
async def get_institution(
    institution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InstitutionResponse:
    """Retrieves an institution by its UUID."""
    if (
        current_user.role != UserRole.PLATFORM_ADMIN
        and current_user.institution_id != institution_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this institution.",
        )

    inst = await db.get(Institution, institution_id)
    if not inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institution not found.",
        )
    return InstitutionResponse.model_validate(inst)


@router.patch("/{institution_id}", response_model=InstitutionResponse)
async def update_institution(
    institution_id: UUID,
    data: InstitutionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InstitutionResponse:
    """Updates institution settings or status."""
    is_platform_admin = current_user.role == UserRole.PLATFORM_ADMIN
    is_inst_admin = (
        current_user.role == UserRole.INST_ADMIN
        and current_user.institution_id == institution_id
    )

    if not (is_platform_admin or is_inst_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update this institution.",
        )

    inst = await db.get(Institution, institution_id)
    if not inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institution not found.",
        )

    update_dict = data.model_dump(exclude_unset=True)

    # Only platform admin can change is_active or is_demo
    if not is_platform_admin:
        update_dict.pop("is_active", None)
        update_dict.pop("is_demo", None)

    for field, val in update_dict.items():
        setattr(inst, field, val)

    await db.commit()
    await db.refresh(inst)
    return InstitutionResponse.model_validate(inst)


@router.post(
    "/{institution_id}/approve",
    response_model=InstitutionResponse,
    dependencies=[Depends(require_role(UserRole.PLATFORM_ADMIN))],
)
async def approve_institution(
    institution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InstitutionResponse:
    """Approves an institution for live production operation."""
    inst = await db.get(Institution, institution_id)
    if not inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institution not found.",
        )

    inst.approved_at = datetime.now(timezone.utc)
    inst.approved_by_id = current_user.id
    inst.is_active = True

    await db.commit()
    await db.refresh(inst)
    return InstitutionResponse.model_validate(inst)
