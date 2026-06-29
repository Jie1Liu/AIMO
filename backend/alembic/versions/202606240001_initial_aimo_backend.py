from __future__ import annotations
"""initial AIMO backend schema

Revision ID: 202606240001
Revises:
Create Date: 2026-06-24
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.types import UserDefinedType


revision: str = "202606240001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


class Vector(UserDefinedType):
    cache_ok = True

    def __init__(self, dimensions: int):
        self.dimensions = dimensions

    def get_col_spec(self, **_: object) -> str:
        return f"vector({self.dimensions})"


def uuid_pk() -> sa.Column:
    return sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    ]


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "companies",
        uuid_pk(),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("website_url", sa.Text()),
        sa.Column("industry", sa.Text()),
        *timestamps(),
    )

    op.create_table(
        "users",
        uuid_pk(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("full_name", sa.Text()),
        sa.Column("role", sa.Text(), nullable=False, server_default="member"),
        *timestamps(),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "products",
        uuid_pk(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_name", sa.Text(), nullable=False),
        sa.Column("one_liner", sa.Text()),
        sa.Column("product_description", sa.Text(), nullable=False),
        sa.Column("target_audience", sa.Text()),
        sa.Column("growth_goal", sa.Text()),
        sa.Column("main_problem", sa.Text()),
        sa.Column("solution", sa.Text()),
        sa.Column("competitors", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("keywords", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("negative_keywords", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        *timestamps(),
    )

    op.create_table(
        "platform_accounts",
        uuid_pk(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", sa.Text(), nullable=False),
        sa.Column("account_label", sa.Text(), nullable=False),
        sa.Column("platform_user_id", sa.Text()),
        sa.Column("platform_username", sa.Text()),
        sa.Column("auth_type", sa.Text(), nullable=False),
        sa.Column("secret_ref", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="connected"),
        sa.Column("daily_send_limit", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("daily_sent_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_reset_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        *timestamps(),
    )

    op.create_table(
        "search_strategies",
        uuid_pk(),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("strategy_type", sa.Text(), nullable=False),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("platforms", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "search_jobs",
        uuid_pk(),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("search_strategy_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("search_strategies.id", ondelete="SET NULL")),
        sa.Column("platform", sa.Text(), nullable=False),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("raw_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "social_items",
        uuid_pk(),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("search_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("search_jobs.id", ondelete="SET NULL")),
        sa.Column("platform", sa.Text(), nullable=False),
        sa.Column("platform_item_id", sa.Text(), nullable=False),
        sa.Column("platform_author_id", sa.Text()),
        sa.Column("author_name", sa.Text()),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("content_url", sa.Text()),
        sa.Column("source_title", sa.Text()),
        sa.Column("source_context", sa.Text()),
        sa.Column("engagement_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("raw_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("content_hash", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("platform", "platform_item_id", "product_id"),
    )

    op.create_table(
        "leads",
        uuid_pk(),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("social_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("social_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", sa.Text(), nullable=False),
        sa.Column("author_name", sa.Text()),
        sa.Column("author_platform_id", sa.Text()),
        sa.Column("intent_type", sa.Text(), nullable=False),
        sa.Column("lead_score", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False, server_default="0"),
        sa.Column("pain_point", sa.Text()),
        sa.Column("user_need", sa.Text()),
        sa.Column("matched_product_value", sa.Text()),
        sa.Column("reason", sa.Text()),
        sa.Column("status", sa.Text(), nullable=False, server_default="new"),
        *timestamps(),
    )

    op.create_table(
        "outreach_messages",
        uuid_pk(),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("selected_platform_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("platform_accounts.id", ondelete="SET NULL")),
        sa.Column("platform", sa.Text(), nullable=False),
        sa.Column("recipient_platform_id", sa.Text()),
        sa.Column("recipient_name", sa.Text()),
        sa.Column("message_type", sa.Text(), nullable=False),
        sa.Column("draft_text", sa.Text(), nullable=False),
        sa.Column("final_text", sa.Text()),
        sa.Column("tone", sa.Text(), nullable=False, server_default="helpful"),
        sa.Column("risk_level", sa.Text(), nullable=False, server_default="medium"),
        sa.Column("policy_notes", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending_review"),
        *timestamps(),
    )

    op.create_table(
        "outreach_logs",
        uuid_pk(),
        sa.Column("outreach_message_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("outreach_messages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("platform_accounts.id", ondelete="SET NULL")),
        sa.Column("platform", sa.Text(), nullable=False),
        sa.Column("send_status", sa.Text(), nullable=False),
        sa.Column("platform_response_id", sa.Text()),
        sa.Column("error_message", sa.Text()),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "product_insights",
        uuid_pk(),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("insight_type", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("evidence_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False, server_default="0"),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "product_recommendations",
        uuid_pk(),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recommendation_type", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text()),
        sa.Column("priority", sa.Text(), nullable=False, server_default="medium"),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "audit_logs",
        uuid_pk(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True)),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True)),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True)),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_index("ix_leads_product_score", "leads", ["product_id", "lead_score"])
    op.create_index("ix_outreach_messages_status", "outreach_messages", ["status"])
    op.create_index("ix_search_jobs_status", "search_jobs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_search_jobs_status", table_name="search_jobs")
    op.drop_index("ix_outreach_messages_status", table_name="outreach_messages")
    op.drop_index("ix_leads_product_score", table_name="leads")
    op.drop_table("audit_logs")
    op.drop_table("product_recommendations")
    op.drop_table("product_insights")
    op.drop_table("outreach_logs")
    op.drop_table("outreach_messages")
    op.drop_table("leads")
    op.drop_table("social_items")
    op.drop_table("search_jobs")
    op.drop_table("search_strategies")
    op.drop_table("platform_accounts")
    op.drop_table("products")
    op.drop_table("users")
    op.drop_table("companies")
