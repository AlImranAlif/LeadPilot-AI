from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class Lead(Base):
    __tablename__ = 'leads'
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(40), default='manual')
    raw_message: Mapped[str] = mapped_column(Text)
    customer_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    service: Mapped[str | None] = mapped_column(String(160), nullable=True)
    budget_bdt: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deadline_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    intent: Mapped[str | None] = mapped_column(String(120), nullable=True)
    score: Mapped[int] = mapped_column(Integer, default=0)
    priority: Mapped[str] = mapped_column(String(15), default='LOW')
    explanations: Mapped[list] = mapped_column(JSON, default=list)
    review_required: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String(25), default='NEW')
    provider: Mapped[str] = mapped_column(String(30), default='demo')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    follow_ups: Mapped[list['FollowUp']] = relationship(back_populates='lead', cascade='all,delete-orphan')

class FollowUp(Base):
    __tablename__ = 'follow_ups'
    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey('leads.id', ondelete='CASCADE'), nullable=False)
    action: Mapped[str] = mapped_column(String(100), default='CONTACT_LEAD')
    status: Mapped[str] = mapped_column(String(25), default='PENDING')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    lead: Mapped[Lead] = relationship(back_populates='follow_ups')

class WebhookReceipt(Base):
    __tablename__ = 'webhook_receipts'
    __table_args__ = (UniqueConstraint('external_event_id', name='uq_external_event_id'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    external_event_id: Mapped[str] = mapped_column(String(120), nullable=False)
    lead_id: Mapped[int] = mapped_column(ForeignKey('leads.id'), nullable=False)
