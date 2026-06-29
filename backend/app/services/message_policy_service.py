from __future__ import annotations
from typing import Optional
import re

from sqlalchemy.orm import Session

from app.models.outreach_message import OutreachMessage


class MessagePolicyService:
    spam_terms = {"guaranteed", "act now", "limited time", "100%", "free money"}
    false_claim_terms = {"we used your product", "i personally tried", "everyone loves"}

    def check_message(
        self,
        db: Session,
        message_text: str,
        *,
        recipient_platform_id: Optional[str],
        current_message_id: Optional[object] = None,
    ) -> tuple[str, dict]:
        lower_text = message_text.lower()
        notes: dict[str, object] = {
            "spam_like_language": sorted(term for term in self.spam_terms if term in lower_text),
            "false_claims": sorted(term for term in self.false_claim_terms if term in lower_text),
            "link_count": len(re.findall(r"https?://", lower_text)),
            "duplicate_message": self._is_duplicate(db, message_text, current_message_id),
            "repeated_contact": self._has_repeated_contact(db, recipient_platform_id, current_message_id),
        }
        risk = "medium"
        if notes["spam_like_language"] or notes["false_claims"] or notes["link_count"] > 1:
            risk = "high"
        if notes["duplicate_message"] or notes["repeated_contact"]:
            risk = "blocked"
        if not any(notes.values()):
            risk = "low"
        return risk, notes

    def _is_duplicate(self, db: Session, message_text: str, current_message_id: Optional[object]) -> bool:
        query = db.query(OutreachMessage).filter(
            (OutreachMessage.final_text == message_text) | (OutreachMessage.draft_text == message_text),
            OutreachMessage.status.in_(["approved", "sent"]),
        )
        if current_message_id is not None:
            query = query.filter(OutreachMessage.id != current_message_id)
        return db.query(query.exists()).scalar()

    def _has_repeated_contact(
        self,
        db: Session,
        recipient_platform_id: Optional[str],
        current_message_id: Optional[object],
    ) -> bool:
        if not recipient_platform_id:
            return False
        query = db.query(OutreachMessage).filter(
            OutreachMessage.recipient_platform_id == recipient_platform_id,
            OutreachMessage.status.in_(["sent", "manual_action_required"]),
        )
        if current_message_id is not None:
            query = query.filter(OutreachMessage.id != current_message_id)
        return db.query(query.exists()).scalar()
