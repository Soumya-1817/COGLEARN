"""
Notifications API Router
========================
Endpoints for managing in-app notifications, read receipts, and user delivery preferences.
"""

from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.notification import NotificationCategory
from app.models.notification_preference import NotificationPreference
from app.models.user import User
from app.schemas.notifications import (
    NotificationPreferenceItem,
    NotificationPreferencesUpdate,
    NotificationResponse,
    UnreadCountResponse,
)
from app.services import notification_service

router = APIRouter()


@router.get("/notifications", response_model=list[NotificationResponse])
async def list_notifications(
    unread_only: bool = False,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List user's in-app notifications, optionally filtered to unread items only.
    """
    return await notification_service.get_notifications(
        db=db,
        institution_id=current_user.institution_id,
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )


@router.get("/notifications/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the count of unread notifications for the user.
    """
    count = await notification_service.get_unread_count(
        db=db,
        institution_id=current_user.institution_id,
        user_id=current_user.id,
    )
    return UnreadCountResponse(unread_count=count)


@router.patch("/notifications/{id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark an individual notification as read.
    """
    try:
        return await notification_service.mark_notification_read(
            db=db,
            institution_id=current_user.institution_id,
            notification_id=id,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/notifications/mark-all-read")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark all notifications for the current user as read.
    """
    updated_count = await notification_service.mark_all_read(
        db=db,
        institution_id=current_user.institution_id,
        user_id=current_user.id,
    )
    return {"message": f"Marked {updated_count} notifications as read.", "count": updated_count}


@router.get("/notifications/preferences", response_model=list[NotificationPreferenceItem])
async def get_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve user's notification preferences across all notification categories.
    """
    stmt = select(NotificationPreference).where(
        and_(
            NotificationPreference.user_id == current_user.id,
            NotificationPreference.institution_id == current_user.institution_id,
        )
    )
    result = await db.execute(stmt)
    prefs = result.scalars().all()

    # If no preferences in DB yet, return default config for all categories
    existing_cats = {p.category.value if hasattr(p.category, "value") else str(p.category): p for p in prefs}
    res = []
    for cat in NotificationCategory:
        if cat.value in existing_cats:
            p = existing_cats[cat.value]
            res.append(
                NotificationPreferenceItem(
                    category=cat.value,
                    in_app_enabled=p.in_app_enabled,
                    email_enabled=p.email_enabled,
                    advance_days=p.advance_days,
                )
            )
        else:
            res.append(
                NotificationPreferenceItem(
                    category=cat.value,
                    in_app_enabled=True,
                    email_enabled=True,
                    advance_days=3,
                )
            )
    return res


@router.put("/notifications/preferences", response_model=list[NotificationPreferenceItem])
async def update_preferences(
    pref_in: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update user notification preferences.
    """
    for item in pref_in.preferences:
        try:
            cat_enum = NotificationCategory(item.category.lower())
        except ValueError:
            continue

        stmt = select(NotificationPreference).where(
            and_(
                NotificationPreference.user_id == current_user.id,
                NotificationPreference.category == cat_enum,
                NotificationPreference.institution_id == current_user.institution_id,
            )
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            existing.in_app_enabled = item.in_app_enabled
            existing.email_enabled = item.email_enabled
            existing.advance_days = item.advance_days
        else:
            new_pref = NotificationPreference(
                id=uuid4(),
                institution_id=current_user.institution_id,
                user_id=current_user.id,
                category=cat_enum,
                in_app_enabled=item.in_app_enabled,
                email_enabled=item.email_enabled,
                advance_days=item.advance_days,
            )
            db.add(new_pref)

    await db.commit()
    return await get_preferences(current_user=current_user, db=db)
