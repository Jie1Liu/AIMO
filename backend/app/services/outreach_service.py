from __future__ import annotations
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError, PolicyError
from app.core.rate_limit import can_send_today
from app.models.lead import Lead
from app.models.outreach_log import OutreachLog
from app.models.outreach_message import OutreachMessage
from app.models.platform_account import PlatformAccount
from app.outbound import get_outbound_connector
from app.schemas.outreach import OutreachMessageCreate
from app.services.message_policy_service import MessagePolicyService


class OutreachService:
    def __init__(self) -> None:
        self.policy = MessagePolicyService()

    def create_message(self, db: Session, lead: Lead, payload: OutreachMessageCreate) -> OutreachMessage:
        lead = (
            db.query(Lead)
            .options(joinedload(Lead.product), joinedload(Lead.social_item))
            .filter(Lead.id == lead.id)
            .one()
        )
        draft_text = self._build_draft(lead, payload.tone)
        risk_level, policy_notes = self.policy.check_message(
            db,
            draft_text,
            recipient_platform_id=lead.author_platform_id,
        )
        message = OutreachMessage(
            product_id=lead.product_id,
            lead_id=lead.id,
            selected_platform_account_id=payload.selected_platform_account_id,
            platform=lead.platform,
            recipient_platform_id=lead.author_platform_id,
            recipient_name=lead.author_name,
            message_type=payload.message_type,
            draft_text=draft_text,
            tone=payload.tone,
            risk_level=risk_level,
            policy_notes=policy_notes,
        )
        db.add(message)
        db.flush()
        return message

    def approve(self, message: OutreachMessage) -> OutreachMessage:
        final_text = message.final_text or message.draft_text
        if message.risk_level in {"high", "blocked"}:
            raise PolicyError("Message risk is too high to approve.")
        message.final_text = final_text
        message.status = "approved"
        return message

    def reject(self, message: OutreachMessage) -> OutreachMessage:
        message.status = "rejected"
        return message

    def send(self, db: Session, message: OutreachMessage) -> tuple[OutreachMessage, OutreachLog, str]:
        message_text = message.final_text or message.draft_text
        if message.status != "approved":
            raise PolicyError("Message must be approved before sending.")

        risk_level, policy_notes = self.policy.check_message(
            db,
            message_text,
            recipient_platform_id=message.recipient_platform_id,
            current_message_id=message.id,
        )
        message.risk_level = risk_level
        message.policy_notes = policy_notes
        if risk_level in {"high", "blocked"}:
            raise PolicyError("Message failed policy checks and cannot be sent.")

        account = self._select_account(db, message)
        if account.status != "connected":
            raise PolicyError("Selected platform account is not connected.")
        if not can_send_today(account):
            raise PolicyError("Selected platform account has reached its daily send limit.")

        connector = get_outbound_connector(message.platform)
        result = connector.send(account, message)
        log = OutreachLog(
            outreach_message_id=message.id,
            platform_account_id=account.id,
            platform=message.platform,
            send_status=result.status,
            platform_response_id=result.platform_response_id,
            error_message=result.error_message,
            sent_at=datetime.now(timezone.utc) if result.status == "sent" else None,
        )
        db.add(log)

        if result.status == "sent":
            account.daily_sent_count += 1
            message.status = "sent"
        else:
            message.status = "manual_action_required"

        db.flush()
        return message, log, result.action

    def _select_account(self, db: Session, message: OutreachMessage) -> PlatformAccount:
        if message.selected_platform_account_id:
            account = db.get(PlatformAccount, message.selected_platform_account_id)
            if not account:
                raise NotFoundError("Selected platform account not found.")
            return account

        account = (
            db.query(PlatformAccount)
            .filter(
                PlatformAccount.platform == message.platform,
                PlatformAccount.status == "connected",
            )
            .order_by(PlatformAccount.daily_sent_count.asc())
            .first()
        )
        if not account:
            raise PolicyError("No connected platform account is available for this platform.")
        message.selected_platform_account_id = account.id
        return account

    def _build_draft(self, lead: Lead, tone: str) -> str:
        product = lead.product
        opener = f"Hi {lead.author_name}," if lead.author_name else "Hi,"
        pain = lead.pain_point or "the problem you described"
        value = lead.matched_product_value or product.one_liner or product.product_description
        return (
            f"{opener} I saw your {lead.platform} post about {pain}. "
            f"{product.product_name} is built around that kind of workflow: {value}. "
            "If it is useful, I can share a short example and you can decide whether it fits. No pressure."
        )
