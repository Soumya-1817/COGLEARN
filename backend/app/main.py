"""
COGLEARN Backend Application Entrypoint
=======================================
Configures FastAPI application, CORS middleware, API v1 routers,
and real-time WebSockets.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
from app.api.v1.websockets import mentor_feed
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks: auto-create tables and seed demo data if database is empty
    try:
        import logging
        from sqlalchemy import select
        from app.core.database import engine, Base, AsyncSessionLocal
        from app.models.institution import Institution
        from app.scripts.seed_demo import seed_demo

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with AsyncSessionLocal() as db:
            existing = await db.execute(select(Institution).limit(1))
            if existing.scalar_one_or_none() is None:
                logging.getLogger(__name__).info("Database empty on startup. Seeding Greenfield University demo data...")
                await seed_demo(db, reset=False)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Startup auto-initialization notice: %s", e)
    yield
    # Shutdown tasks


app = FastAPI(
    title="COGLEARN API",
    version="1.0.0",
    description="Intelligent Learning and Cognitive Risk Management Platform",
    lifespan=lifespan,
)

# CORS Middleware Configuration
cors_origins = settings.backend_cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else ["*"],
    allow_origin_regex=r"^https?://(localhost|.*\.onrender\.com|.*\.vercel\.app|.*\.netlify\.app)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(institutions.router, prefix="/api/v1/institutions", tags=["Institutions"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(lms.router, prefix="/api/v1", tags=["LMS"])
app.include_router(activity.router, prefix="/api/v1", tags=["Activity"])
app.include_router(tasks.router, prefix="/api/v1", tags=["Task Queue"])
app.include_router(calendar.router, prefix="/api/v1", tags=["Calendar"])
app.include_router(notifications.router, prefix="/api/v1", tags=["Notifications"])
app.include_router(mentor.router, prefix="/api/v1", tags=["Mentor"])
app.include_router(admin_analytics.router, prefix="/api/v1", tags=["Admin Analytics"])
app.include_router(my_analytics.router, prefix="/api/v1", tags=["My Analytics"])
app.include_router(students.router, prefix="/api/v1", tags=["Students"])

# WebSocket Endpoints
app.add_api_websocket_route("/ws/mentor/{mentor_id}", mentor_feed.mentor_ws_endpoint)


@app.get("/health", tags=["System"])
async def health_check():
    """System health check endpoint for container orchestrators and load balancers."""
    return {
        "status": "ok",
        "service": "coglearn-api",
        "environment": settings.ENVIRONMENT,
    }
