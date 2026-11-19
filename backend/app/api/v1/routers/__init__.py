"""
API v1 Routers Package
"""

from app.api.v1.routers import (
    activity,
    admin_analytics,
    auth,
    calendar,
    institutions,
    lms,
    mentor,
    my_analytics,
    notifications,
    students,
    tasks,
    users,
)

__all__ = [
    "auth",
    "institutions",
    "users",
    "lms",
    "activity",
    "tasks",
    "calendar",
    "notifications",
    "mentor",
    "admin_analytics",
    "my_analytics",
    "students",
]
