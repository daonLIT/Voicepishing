from fastapi import APIRouter
from app.db.base import SessionLocal
from app.db.models import PoliceEducation, EducationAssignment

router = APIRouter()

@router.get("/")
def list_education():
    db = SessionLocal()
    rows = db.query(PoliceEducation).all()
    out = [dict(id=r.id, title=r.title, rules=r.rules) for r in rows]
    db.close()
    return out

@router.get("/assignments")
def list_assignments():
    db = SessionLocal()
    rows = db.query(EducationAssignment).all()
    out = [dict(id=r.id, education_id=r.education_id, victim_id=r.victim_id) for r in rows]
    db.close()
    return out
