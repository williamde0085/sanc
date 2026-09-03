import uuid

from fastapi import Depends, FastAPI, Header, HTTPException

from screening import audit, db
from screening.config import API_KEY, MATCH_THRESHOLD, MAX_CANDIDATES, REQUIRE_SECONDARY, REVIEW_THRESHOLD
from screening.matcher import classify, score_candidate
from screening.models import Query
from screening.normalize import normalize_name
from screening.schemas import CandidateOut, ReviewRequest, ScreenRequest, ScreenResponse

app = FastAPI(title="sanctions screening", version="0.1.0")


def require_api_key(x_api_key: str | None = Header(default=None)):
    # TODO: сравнивать через hmac.compare_digest
    if not API_KEY or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="bad api key")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    try:
        with db.connect() as conn, conn.cursor() as cur:
            cur.execute("select count(*) as n from sanction_entries")
            n = cur.fetchone()["n"]
    except Exception as e:
        raise HTTPException(status_code=503, detail="db недоступна") from e
    return {"status": "ready", "entities": n}


@app.post("/v1/screen", response_model=ScreenResponse, dependencies=[Depends(require_api_key)])
def screen(req: ScreenRequest, x_request_id: str | None = Header(default=None)):
    normalized = normalize_name(req.name)
    if not normalized:
        raise HTTPException(status_code=422, detail="имя не нормализуется")

    request_id = x_request_id or str(uuid.uuid4())
    query = Query(name=req.name, country=req.country, date_of_birth=req.date_of_birth,
                  identifier=req.identifier, entity_type=req.entity_type)

    with db.connect() as conn:
        candidates = db.find_candidates(conn, normalized, MAX_CANDIDATES)
        scored = sorted((score_candidate(query, c) for c in candidates),
                        key=lambda s: s.score, reverse=True)
        outcome, reasons = classify(scored, REVIEW_THRESHOLD, MATCH_THRESHOLD, REQUIRE_SECONDARY)

        out = [
            CandidateOut(
                entity_id=s.candidate.entity_id,
                primary_name=s.candidate.primary_name,
                matched_name=s.matched_name,
                source_list=s.candidate.source_list,
                entity_type=s.candidate.entity_type,
                score=s.score,
                name_score=s.name_score,
                reason_codes=list(s.reason_codes),
            )
            for s in scored[:10] if s.score >= REVIEW_THRESHOLD
        ]
        list_version = db.current_list_version(conn)
        decision_id = audit.record_decision(
            conn, request_id, normalized, list_version, outcome,
            scored[0].score if scored else None, reasons,
            [c.model_dump() for c in out], outcome == "POSSIBLE_MATCH",
        )

    return ScreenResponse(
        decision_id=decision_id,
        request_id=request_id,
        outcome=outcome,
        list_version=list_version,
        reason_codes=list(reasons),
        candidates=out,
        human_review_required=outcome == "POSSIBLE_MATCH",
    )


@app.get("/v1/decisions/{decision_id}", dependencies=[Depends(require_api_key)])
def decision(decision_id: str):
    with db.connect() as conn:
        row = db.get_decision(conn, decision_id)
    if row is None:
        raise HTTPException(status_code=404, detail="решение не найдено")
    return row


@app.post("/v1/reviews/{decision_id}", dependencies=[Depends(require_api_key)])
def submit_review(decision_id: str, req: ReviewRequest, x_reviewer: str | None = Header(default=None)):
    if not x_reviewer or len(x_reviewer.strip()) < 3:
        raise HTTPException(status_code=400, detail="нужен заголовок X-Reviewer")
    with db.connect() as conn:
        ok = audit.record_review(conn, decision_id, x_reviewer.strip(), req.outcome, req.notes)
    if not ok:
        raise HTTPException(status_code=409, detail="решение не найдено или уже отревьюено")
    return {"status": "ok", "decision_id": decision_id}


@app.get("/v1/audit/verify", dependencies=[Depends(require_api_key)])
def verify_audit():
    with db.connect() as conn:
        result = audit.verify_chains(conn)
    if not result["valid"]:
        raise HTTPException(status_code=503, detail=result)
    return result


def run():
    import uvicorn
    uvicorn.run("screening.api:app", host="0.0.0.0", port=8090)
