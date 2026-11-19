from contextvars import ContextVar
from uuid import UUID

current_tenant_id: ContextVar[str | None] = ContextVar("current_tenant_id", default=None)


def set_current_tenant_id(tenant_id: str | UUID | None) -> None:
    """Sets the current tenant ID in the context var for multi-tenant isolation."""
    if tenant_id is None:
        current_tenant_id.set(None)
    else:
        current_tenant_id.set(str(tenant_id))


def get_current_tenant_id() -> str | None:
    """Retrieves the current tenant ID from context."""
    return current_tenant_id.get(None)
