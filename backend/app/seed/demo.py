from __future__ import annotations
from typing import Optional
from app.core.database import SessionLocal
from app.models.company import Company
from app.models.lead import Lead
from app.models.platform_account import PlatformAccount
from app.models.product import Product
from app.schemas.outreach import OutreachMessageCreate
from app.services.outreach_service import OutreachService
from app.services.product_advisor_service import ProductAdvisorService
from app.services.search_orchestrator import SearchOrchestrator
from app.services.search_strategy_service import SearchStrategyService


def seed_demo() -> None:
    db = SessionLocal()
    try:
        existing = db.query(Product).filter(Product.product_name == "AIMO").one_or_none()
        if existing:
            print(f"Demo product already exists: {existing.id}")
            return

        company = Company(
            name="AIMO Demo Co",
            website_url="https://example.com",
            industry="B2B SaaS",
        )
        db.add(company)
        db.flush()

        product = Product(
            company_id=company.id,
            product_name="AIMO",
            one_liner="AI CMO for early-stage founders",
            product_description="AIMO helps companies discover potential customers from public social media discussions.",
            target_audience="early-stage SaaS founders, indie hackers, small business owners",
            growth_goal="find early users and validate product positioning",
            main_problem="Founders do not know where to find their first users.",
            solution="AIMO searches public discussions, identifies leads, and generates human-reviewed outreach drafts.",
            competitors=["Apollo", "Buffer", "Hootsuite"],
            keywords=["find early users", "startup marketing", "social listening"],
            negative_keywords=["job", "internship", "course"],
        )
        db.add(product)
        db.flush()

        accounts = [
            PlatformAccount(
                company_id=company.id,
                platform="reddit",
                account_label="Founder Reddit",
                platform_username="aimo_founder",
                auth_type="manual",
                secret_ref=f"aimo/{company.id}/reddit/founder",
                daily_send_limit=5,
            ),
            PlatformAccount(
                company_id=company.id,
                platform="youtube",
                account_label="AIMO YouTube",
                platform_username="@aimo",
                auth_type="oauth",
                secret_ref=f"aimo/{company.id}/youtube/main",
                daily_send_limit=10,
            ),
            PlatformAccount(
                company_id=company.id,
                platform="bluesky",
                account_label="AIMO Bluesky",
                platform_username="aimo.bsky.social",
                auth_type="app_password",
                secret_ref=f"aimo/{company.id}/bluesky/main",
                daily_send_limit=12,
            ),
        ]
        db.add_all(accounts)
        db.flush()

        SearchStrategyService().generate_for_product(db, product)
        SearchOrchestrator().run_for_product(db, product, process_now=True)
        lead = db.query(Lead).filter(Lead.product_id == product.id).order_by(Lead.lead_score.desc()).first()
        if lead:
            OutreachService().create_message(db, lead, payload=OutreachMessageCreate())
        ProductAdvisorService().generate(db, product)

        db.commit()
        print(f"Seeded demo product: {product.id}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo()
