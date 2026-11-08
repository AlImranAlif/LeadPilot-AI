from dataclasses import dataclass
from app.schemas import ExtractedFields

@dataclass(frozen=True)
class ScoreResult:
    score: int
    priority: str
    reasons: list[str]
    review_required: bool

def evaluate(fields: ExtractedFields) -> ScoreResult:
    """Explicit, auditable business rules; not a prediction or an LLM output."""
    score = 0
    reasons: list[str] = []
    if fields.service:
        score += 25
        reasons.append('+25: specific service identified')
    else:
        reasons.append('+0: service not identified')
    if fields.budget_bdt is not None:
        if fields.budget_bdt >= 50000:
            score += 30
            reasons.append('+30: budget meets 50,000 BDT threshold')
        elif fields.budget_bdt >= 15000:
            score += 15
            reasons.append('+15: budget is between 15,000 and 49,999 BDT')
        else:
            reasons.append('+0: budget below 15,000 BDT')
    else:
        reasons.append('+0: budget not supplied')
    if fields.deadline_days is not None:
        if fields.deadline_days <= 30:
            score += 20
            reasons.append('+20: deadline within 30 days')
        elif fields.deadline_days <= 90:
            score += 10
            reasons.append('+10: deadline within 90 days')
        else:
            reasons.append('+0: long-term deadline')
    else:
        reasons.append('+0: deadline not supplied')
    if fields.intent == 'REQUEST_QUOTE':
        score += 25
        reasons.append('+25: explicit quotation or purchase intent')
    elif fields.intent == 'INQUIRY':
        score += 10
        reasons.append('+10: general buying inquiry')
    else:
        reasons.append('+0: intent unclear')
    needs_review = not fields.service or fields.budget_bdt is None or fields.intent is None
    if needs_review:
        reasons.append('Human review: missing service, budget, or intent')
    priority = 'HIGH' if score >= 75 and not needs_review else 'MEDIUM' if score >= 45 else 'LOW'
    return ScoreResult(score, priority, reasons, needs_review)
