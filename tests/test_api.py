from app.extraction import local_extract
from app.scoring import evaluate

MESSAGE = 'I need an e-commerce website. Budget is 80000 BDT and I need it within 3 weeks. Please send a quotation.'

def test_extraction_and_explainable_score():
    fields=local_extract(MESSAGE)
    assert fields.budget_bdt==80000
    assert fields.deadline_days==21
    assert fields.service=='E-commerce development'
    result=evaluate(fields)
    assert result.score==100
    assert result.priority=='HIGH'
    assert not result.review_required

def test_analyze_creates_followup_and_persists(client):
    r=client.post('/api/leads/analyze',json={'message':MESSAGE,'customer_name':'Test customer'})
    assert r.status_code==201,r.text
    data=r.json()
    assert data['lead']['priority']=='HIGH'
    assert data['follow_up_created'] is True
    assert data['extraction_mode']=='demo_rules'
    lead_id=data['lead']['id']
    assert client.get(f'/api/leads/{lead_id}').json()['id']==lead_id
    assert len(client.get('/api/follow-ups').json())==1
    assert client.get('/api/analytics/summary').json()['high_priority']==1

def test_missing_fields_are_flagged(client):
    r=client.post('/api/leads/analyze',json={'message':'Hello, please call me so we can discuss a potential project.'})
    assert r.status_code==201
    assert r.json()['lead']['review_required'] is True
    assert not r.json()['follow_up_created']

def test_invalid_input_and_404(client):
    assert client.post('/api/leads/analyze',json={'message':'  '}).status_code==422
    assert client.get('/api/leads/9999').status_code==404
    assert client.patch('/api/leads/9999',json={'status':'CONTACTED'}).status_code==404
    assert client.get('/api/leads?priority=CRITICAL').status_code==422

def test_webhook_idempotency(client):
    payload={'event_id':'source-event-123','message':MESSAGE}
    a=client.post('/api/webhooks/inquiries',json=payload)
    b=client.post('/api/webhooks/inquiries',json=payload)
    assert a.status_code==200
    assert b.status_code==200
    assert a.json()['lead']['id']==b.json()['lead']['id']
    assert b.json()['replayed'] is True
    assert client.get('/api/analytics/summary').json()['total']==1
    assert len(client.get('/api/follow-ups').json())==1

def test_status_change(client):
    lead=client.post('/api/leads/analyze',json={'message':MESSAGE}).json()['lead']
    r=client.patch(f"/api/leads/{lead['id']}",json={'status':'CONTACTED'})
    assert r.status_code==200
    assert r.json()['status']=='CONTACTED'
    assert client.get(f"/api/leads/{lead['id']}/explanation").json()['score']==100
