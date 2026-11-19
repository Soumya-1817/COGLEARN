from collections.abc import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.core.tenant import current_tenant_id

if "sqlite" in settings.database_url:
    engine = create_async_engine(
        settings.database_url,
        echo=settings.environment == "development",
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_async_engine(
        settings.database_url,
        echo=settings.environment == "development",
        pool_size=20,
        max_overflow=40,
    )

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy 2.0 declarative models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session configured with multi-tenant context."""
    async with AsyncSessionLocal() as session:
        tenant = current_tenant_id.get(None)
        if tenant and "postgresql" in str(engine.url):
            # Set PostgreSQL session local variable for tenant isolation / RLS
            clean_tenant = str(tenant).replace("'", "''")
            await session.execute(text(f"SET LOCAL app.current_tenant_id = '{clean_tenant}'"))
        try:
            yield session
        finally:
            await session.close()

