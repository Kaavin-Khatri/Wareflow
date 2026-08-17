"""Health-check router — no business logic, just a liveness probe."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Return service liveness status. Used by Render and monitoring tools."""
    return {"status": "ok"}
