from __future__ import annotations
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    companies,
    health,
    insights,
    integrations,
    leads,
    outreach,
    platform_accounts,
    products,
    search_jobs,
)
from app.core.config import settings
from app.core.database import initialize_database
from app.core.exceptions import install_exception_handlers


def create_app() -> FastAPI:
    app = FastAPI(
        title="AIMO Backend",
        version="1.0.0",
        description="AI CMO backend for lead discovery, reviewed outreach, and product intelligence.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    install_exception_handlers(app)

    @app.on_event("startup")
    def initialize_demo_database() -> None:
        initialize_database()

    app.include_router(health.router)
    app.include_router(integrations.router)
    app.include_router(companies.router, prefix="/api/companies", tags=["Companies"])
    app.include_router(products.router, prefix="/api/products", tags=["Products"])
    app.include_router(platform_accounts.router, tags=["Platform Accounts"])
    app.include_router(search_jobs.router, prefix="/api/search-jobs", tags=["Search Jobs"])
    app.include_router(leads.router, tags=["Leads"])
    app.include_router(outreach.router, tags=["Outreach"])
    app.include_router(insights.router, tags=["Insights"])

    return app


app = create_app()
