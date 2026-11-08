from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.config import get_settings
from app.database import Base, engine, get_db
from app.models import Lead, FollowUp, WebhookReceipt
from app.schemas import (AnalyzeRequest, WebhookRequest, LeadOut, AnalyzeResult,
                         LeadPatch, FollowUpOut, SummaryOut)
from app.extraction import extract
from app.scoring import evaluate

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title='LeadPilot AI API', version='1.0.0',
              description=('Explainable lead scoring and CRM workflow automation. '
                           'The default demo extractor is rule-based, not AI. Set EXTRACTION_PROVIDER=gemini '
                           'and provide a Gemini key for real LLM extraction.'),
              lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[s.strip() for s in settings.cors_origins.split(',') if s.strip()],
                   allow_credentials=False, allow_methods=['GET','POST','PATCH'],allow_headers=['*'])

def auth(x_api_key: str | None = Header(default=None)):
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(401,'Valid X-API-Key header required')

def format_result(lead: Lead, replayed=False, has_follow_up=False) -> AnalyzeResult:
    return AnalyzeResult(lead=LeadOut.model_validate(lead), follow_up_created=has_follow_up,
                         extraction_mode=lead.provider, replayed=replayed)

async def process(message: str, customer_name: str | None, email: str | None, source: str, db: Session):
    fields, provider = await extract(message,settings)
    decision = evaluate(fields)
    lead = Lead(raw_message=message,customer_name=customer_name,email=email,source=source,
                service=fields.service,budget_bdt=fields.budget_bdt,deadline_days=fields.deadline_days,
                intent=fields.intent,score=decision.score,priority=decision.priority,
                explanations=decision.reasons,review_required=decision.review_required,provider=provider)
    db.add(lead)
    db.flush()
    follow_up_created = lead.priority == 'HIGH'
    if follow_up_created:
        db.add(FollowUp(lead_id=lead.id,action='CONTACT_HIGH_PRIORITY_LEAD'))
    return lead, follow_up_created

@app.get('/', include_in_schema=False)
def index():
    return FileResponse(Path(__file__).parent / 'static' / 'index.html')

@app.get('/health', tags=['Health'])
def health():
    return {'status':'ok','extractor':settings.extraction_provider}

@app.post('/api/leads/analyze',response_model=AnalyzeResult,status_code=201,tags=['Automation'], dependencies=[Depends(auth)])
async def analyze(body: AnalyzeRequest,db: Session=Depends(get_db)):
    lead,follow_up = await process(body.message,body.customer_name,body.email,'manual',db)
    db.commit()
    db.refresh(lead)
    return format_result(lead,has_follow_up=follow_up)

@app.post('/api/webhooks/inquiries',response_model=AnalyzeResult,tags=['Automation'], dependencies=[Depends(auth)])
async def webhook(body: WebhookRequest,db: Session=Depends(get_db)):
    existing = db.scalar(select(WebhookReceipt).where(WebhookReceipt.external_event_id==body.event_id))
    if existing:
        lead = db.get(Lead,existing.lead_id)
        return format_result(lead,replayed=True,has_follow_up=bool(lead.follow_ups))
    lead,follow_up = await process(body.message,body.customer_name,body.email,'webhook',db)
    db.add(WebhookReceipt(external_event_id=body.event_id,lead_id=lead.id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(select(WebhookReceipt).where(WebhookReceipt.external_event_id==body.event_id))
        if existing:
            saved = db.get(Lead,existing.lead_id)
            return format_result(saved,replayed=True,has_follow_up=bool(saved.follow_ups))
        raise
    db.refresh(lead)
    return format_result(lead,has_follow_up=follow_up)

@app.get('/api/leads',response_model=list[LeadOut],tags=['CRM'],dependencies=[Depends(auth)])
def list_leads(status: str | None=Query(default=None), priority: str | None=Query(default=None),
               q: str | None=Query(default=None,max_length=120), limit: int=Query(default=50,ge=1,le=200),
               offset: int=Query(default=0,ge=0),db: Session=Depends(get_db)):
    stmt = select(Lead)
    if status:
        if status not in {'NEW','CONTACTED','QUALIFIED','CLOSED'}:
            raise HTTPException(422,'Invalid status filter')
        stmt=stmt.where(Lead.status==status)
    if priority:
        if priority not in {'HIGH','MEDIUM','LOW'}:
            raise HTTPException(422,'Invalid priority filter')
        stmt=stmt.where(Lead.priority==priority)
    if q:
        term=f'%{q}%'
        stmt=stmt.where((Lead.raw_message.ilike(term)) | (Lead.customer_name.ilike(term)))
    return db.scalars(stmt.order_by(Lead.id.desc()).offset(offset).limit(limit)).all()

@app.get('/api/leads/{lead_id}',response_model=LeadOut,tags=['CRM'],dependencies=[Depends(auth)])
def get_lead(lead_id: int,db: Session=Depends(get_db)):
    lead=db.get(Lead,lead_id)
    if not lead:
        raise HTTPException(404,'Lead not found')
    return lead

@app.patch('/api/leads/{lead_id}',response_model=LeadOut,tags=['CRM'],dependencies=[Depends(auth)])
def update_lead(lead_id: int,body: LeadPatch,db: Session=Depends(get_db)):
    lead=db.get(Lead,lead_id)
    if not lead:
        raise HTTPException(404,'Lead not found')
    lead.status=body.status
    db.commit()
    db.refresh(lead)
    return lead

@app.get('/api/leads/{lead_id}/explanation',tags=['CRM'],dependencies=[Depends(auth)])
def explain(lead_id: int,db: Session=Depends(get_db)):
    lead=db.get(Lead,lead_id)
    if not lead:
        raise HTTPException(404,'Lead not found')
    return {'lead_id':lead.id,'score':lead.score,'priority':lead.priority,
            'rules':lead.explanations,'review_required':lead.review_required,
            'note':'Rule-based business score, not model certainty or conversion probability.'}

@app.get('/api/follow-ups',response_model=list[FollowUpOut],tags=['Automation'],dependencies=[Depends(auth)])
def list_followups(db: Session=Depends(get_db)):
    return db.scalars(select(FollowUp).order_by(FollowUp.id.desc()).limit(200)).all()

@app.get('/api/analytics/summary',response_model=SummaryOut,tags=['Analytics'],dependencies=[Depends(auth)])
def summary(db: Session=Depends(get_db)):
    statuses={s:n for s,n in db.execute(select(Lead.status,func.count(Lead.id)).group_by(Lead.status)).all()}
    return SummaryOut(total=sum(statuses.values()),
        high_priority=db.scalar(select(func.count()).select_from(Lead).where(Lead.priority=='HIGH')),
        needs_review=db.scalar(select(func.count()).select_from(Lead).where(Lead.review_required.is_(True))),
        pending_follow_ups=db.scalar(select(func.count()).select_from(FollowUp).where(FollowUp.status=='PENDING')),
        by_status=statuses)
