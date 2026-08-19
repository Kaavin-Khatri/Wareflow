"""
WareFlow API — FastAPI backend.

SOLID architecture:
  routers → services → repositories(interfaces) → repositories(impl)

Routers handle HTTP concerns only. Business logic lives in services.
Repositories implement data-access contracts defined by interfaces.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import (
    alerts,
    audit,
    business_settings,
    categories,
    customers,
    deliveries,
    health,
    inquiries,
    invoices,
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
    staff,
    stock,
    stock_analytics,
    suppliers,
    two_factor,
    uom,
)
from app.core.config import get_settings


def create_app() -> FastAPI:
    """Application factory — assembles the FastAPI app with middleware and routers."""
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="AI-assisted wholesale inventory management API",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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
    application.include_router(purchase_orders.router)
    application.include_router(purchase_returns.router)
    application.include_router(business_settings.router)
    application.include_router(alerts.router)

    return application


app = create_app()
