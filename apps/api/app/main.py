"""
WareFlow API — FastAPI backend.

SOLID architecture:
  routers → services → repositories(interfaces) → repositories(impl)

Routers handle HTTP concerns only. Business logic lives in services.
Repositories implement data-access contracts defined by interfaces.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import health


def create_app() -> FastAPI:
    """Application factory — assembles the FastAPI app with middleware and routers."""
    application = FastAPI(
        title="WareFlow API",
        version="0.1.0",
        description="AI-assisted wholesale inventory management API",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health.router)

    return application


app = create_app()
