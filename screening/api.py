from fastapi import Depends, FastAPI, Header, HTTPException

from screening.config import API_KEY
from screening.schemas import ReviewRequest, ScreenRequest, ScreenResponse

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
    raise NotImplementedError


@app.post("/v1/screen", response_model=ScreenResponse, dependencies=[Depends(require_api_key)])
def screen(req: ScreenRequest, x_request_id: str | None = Header(default=None)) -> ScreenResponse:
    raise NotImplementedError


@app.get("/v1/decisions/{decision_id}", dependencies=[Depends(require_api_key)])
def get_decision(decision_id: str):
    raise NotImplementedError


@app.post("/v1/reviews/{decision_id}", dependencies=[Depends(require_api_key)])
def submit_review(decision_id: str, req: ReviewRequest, x_reviewer: str | None = Header(default=None)):
    raise NotImplementedError


@app.get("/v1/audit/verify", dependencies=[Depends(require_api_key)])
def verify_audit():
    raise NotImplementedError


def run():
    import uvicorn
    uvicorn.run("screening.api:app", host="0.0.0.0", port=8090)
