"""Health-check router — liveness and database connectivity probes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db_session

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Return service liveness status. Used by Render and monitoring tools."""
    return {"status": "ok"}


@router.get("/health/db")
def db_health_check(session: Session = Depends(get_db_session)) -> dict[str, str]:
    """
    Verify database connectivity through the session dependency.

    Executes a SELECT 1 query over the active database connection.
    """
    try:
        result = session.execute(text("SELECT 1")).scalar()
        if result == 1:
            return {"status": "ok", "database": "connected"}
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database query returned unexpected result",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {exc}",
        ) from exc
