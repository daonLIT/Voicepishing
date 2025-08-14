from fastapi import APIRouter
from app.db.base import SessionLocal
from app.db.models import AgentProfile, AttackMethod

router = APIRouter()

@router.get("/victims")
def victims():
    db = SessionLocal()
    rows = db.query(AgentProfile).filter(AgentProfile.role=="victim").all()
    out = [dict(id=r.id, age_group=r.age_group, traits=r.traits) for r in rows]
    db.close()
    return out

@router.get("/methods")
def methods():
    db = SessionLocal()
    rows = db.query(AttackMethod).all()
    out = [dict(id=r.id, code=r.code, name=r.name) for r in rows]
    db.close()
    return out
