"""
WareFlow API — FastAPI backend.

SOLID architecture:
  routers → services → repositories(interfaces) → repositories(impl)

Routers handle HTTP concerns only. Business logic lives in services.
Repositories implement data-access contracts defined by interfaces.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.routers import (
    alerts,
    analytics,
    audit,
    business_settings,
    categories,
    customers,
    deliveries,
    health,
    inquiries,
    invoices,
    leads,
    me,
    notifications,
    portal,
    products,
    profiles,
    purchase_orders,
    purchase_returns,
    retailers,
    roles,
    sales_orders,
    sales_returns,
    search,
    staff,
    stock,
    stock_analytics,
    supplier_portal,
    suppliers,
    two_factor,
    uom,
)
from app.core.config import get_settings
from app.core.di import get_alert_scheduler
from app.core.limiter import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup & shutdown hooks (APScheduler background worker)."""
    try:
        from app.db.session import get_engine
        from app.models import Base

        engine = get_engine()
        Base.metadata.create_all(bind=engine)
    except Exception as exc:
        import logging

        logging.getLogger(__name__).warning("Database schema init notice: %s", exc)

    scheduler = get_alert_scheduler()
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown()


def create_app() -> FastAPI:
    """Application factory — assembles the FastAPI app with middleware and routers."""
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="AI-assisted wholesale inventory management API",
        lifespan=lifespan,
    )

    # Rate limiting (SlowAPI)
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    application.add_middleware(SlowAPIMiddleware)

    # Cross-Origin Resource Sharing (CORS)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins if isinstance(settings.allowed_origins, list) else [settings.allowed_origins],
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    @application.get(
        "/",
        tags=["Health & Diagnostics"],
        summary="Root API overview and system status",
    )
    def root_overview() -> dict[str, str]:
        """Root API landing endpoint providing system status and documentation URLs."""
        return {
            "name": settings.app_name,
            "version": "0.1.0",
            "status": "healthy",
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
            "health": "/health",
        }

    @application.get("/favicon.ico", include_in_schema=False)
    def favicon_handler() -> Response:
        """Silent 204 handler for browser favicon requests."""
        return Response(status_code=204)

    application.include_router(health.router)
    application.include_router(me.router)
    application.include_router(profiles.router)
    application.include_router(staff.router)
    application.include_router(roles.router)
    application.include_router(two_factor.router)
    application.include_router(audit.router)
    application.include_router(products.router)
    application.include_router(categories.router)
    application.include_router(uom.router)
    application.include_router(stock.router)
    application.include_router(stock_analytics.router)
    application.include_router(analytics.router)
    application.include_router(retailers.router)
    application.include_router(customers.router)
    application.include_router(sales_orders.router)
    application.include_router(invoices.router)
    application.include_router(deliveries.router)
    application.include_router(sales_returns.router)
    application.include_router(portal.router)
    application.include_router(inquiries.router)
    application.include_router(notifications.router)

    application.include_router(suppliers.router)
    application.include_router(supplier_portal.router)
    application.include_router(purchase_orders.router)
    application.include_router(purchase_returns.router)
    application.include_router(business_settings.router)
    application.include_router(alerts.router)
    application.include_router(search.router)
    application.include_router(leads.router)

    return application


app = create_app()
