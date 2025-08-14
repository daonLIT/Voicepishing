from fastapi import APIRouter
from app.db.base import SessionLocal
from app.db.models import Outcome

router = APIRouter()

@router.get("/summary")
def summary():
    db = SessionLocal()
    outs = db.query(Outcome).all()
    n = len(outs)
    rate = sum(1 for o in outs if o.is_phished)/n if n else 0.0
    db.close()
    return {"attempts": n, "overall_rate": rate}
