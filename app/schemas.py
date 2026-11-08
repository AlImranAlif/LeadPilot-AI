from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class AnalyzeRequest(BaseModel):
    message: str = Field(min_length=12, max_length=5000, examples=['I need an e-commerce website for my shop. My budget is 80000 BDT and I need it within 3 weeks.'])
    customer_name: str | None = Field(default=None, max_length=120)
    email: str | None = Field(default=None, max_length=254)
    @field_validator('message')
    @classmethod
    def message_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Message must not be blank')
        return v.strip()

class WebhookRequest(AnalyzeRequest):
    event_id: str = Field(min_length=1, max_length=120)

class ExtractedFields(BaseModel):
    service: str | None = Field(default=None, max_length=160)
    budget_bdt: int | None = Field(default=None, ge=0, le=100000000)
    deadline_days: int | None = Field(default=None, ge=1, le=3650)
    intent: str | None = Field(default=None, max_length=120)

class LeadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source: str
    raw_message: str
    customer_name: str | None
    email: str | None
    service: str | None
    budget_bdt: int | None
    deadline_days: int | None
    intent: str | None
    score: int
    priority: str
    explanations: list[str]
    review_required: bool
    status: str
    provider: str
    created_at: datetime

class AnalyzeResult(BaseModel):
    lead: LeadOut
    follow_up_created: bool
    extraction_mode: str
    replayed: bool = False

class LeadPatch(BaseModel):
    status: Literal['NEW','CONTACTED','QUALIFIED','CLOSED']

class FollowUpOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    lead_id: int
    action: str
    status: str
    created_at: datetime

class SummaryOut(BaseModel):
    total: int
    high_priority: int
    needs_review: int
    pending_follow_ups: int
    by_status: dict[str,int]
