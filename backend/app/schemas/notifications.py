"""
Pydantic Schemas for Notifications & Preferences
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    recipient_id: UUID
    category: str
    title: str
    body: str
    priority: str
    is_read: bool
    read_at: Optional[datetime] = None
    action_url: Optional[str] = None
    source_id: Optional[UUID] = None
    created_at: datetime


class UnreadCountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    unread_count: int


class NotificationPreferenceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    category: str
    in_app_enabled: bool = True
    email_enabled: bool = True
    advance_days: int = Field(default=3, ge=1, le=14)


class NotificationPreferencesUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    preferences: list[NotificationPreferenceItem]
