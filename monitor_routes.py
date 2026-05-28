from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import monitor_db

router = APIRouter(prefix="/monitor", tags=["monitor"])


@router.get("/stats")
def stats():
    return monitor_db.get_stats()


@router.get("/runs")
def runs(
    limit:         int  = Query(50, ge=1, le=200),
    offset:        int  = Query(0, ge=0),
    escalated_only: bool = Query(False),
):
    return monitor_db.get_runs(limit=limit, offset=offset, escalated_only=escalated_only)


@router.get("/runs/{run_id}")
def run_detail(run_id: str):
    run = monitor_db.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


class FeedbackRequest(BaseModel):
    run_id:     str
    restaurant: str
    rating:     int   # 1 = thumbs up, -1 = thumbs down


@router.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    if req.rating not in (1, -1):
        raise HTTPException(status_code=400, detail="rating must be 1 or -1")
    monitor_db.save_feedback(req.run_id, req.restaurant, req.rating)
    return {"ok": True}
