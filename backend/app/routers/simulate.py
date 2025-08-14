from fastapi import APIRouter
from uuid import uuid4
from app.schemas.simulation import RunRequest, RunSummary
from app.db.base import SessionLocal
from app.db.models import (SimRun, SimIteration, AttackMethod, AgentProfile,
                           PoliceEducation, EducationAssignment, VictimMemory, Outcome)
from app.services.orchestrator import run_iteration
from app.services.med_trainer import med_generate

router = APIRouter()

@router.post("/run", response_model=RunSummary)
async def simulate(req: RunRequest):
    db = SessionLocal()
    run = SimRun(id=uuid4(), total_rounds=req.rounds); db.add(run); db.commit(); db.refresh(run)

    methods = [dict(id=m.id, code=m.code, name=m.name) for m in db.query(AttackMethod).filter(AttackMethod.id.in_(req.method_ids)).all()]
    victims = [dict(id=v.id, age_group=v.age_group, traits=v.traits) for v in db.query(AgentProfile).filter(AgentProfile.id.in_(req.victim_ids)).all()]

    # 1) Pre
    rules_map = {}  # victim_id -> rules
    pre_results = []
    for r in range(req.rounds):
        it = SimIteration(run_id=run.id, round_index=r, status="pre"); db.add(it); db.commit()
        pre_results += await run_iteration(methods, victims, rules_map, "pre_edu", db)

    # 실패 근거 텍스트 모음
    fail_reasons = [res["outcome"]["rationale"] for res in pre_results if res["outcome"]["is_phished"]]
    if fail_reasons:
        edu = med_generate("\n".join(fail_reasons))
        edu_row = PoliceEducation(run_id=run.id, title="예방교육 v1", content_md=edu["content_md"], rules=edu["rules"])
        db.add(edu_row); db.commit(); db.refresh(edu_row)
        for v in victims:
            db.add(EducationAssignment(education_id=edu_row.id, victim_id=v["id"]))
            db.add(VictimMemory(victim_id=v["id"], education_ids=[edu_row.id],
                                keywords=[k for r in edu["rules"] for k in r.get("keywords",[])]))
            # 메모리 즉시 반영
            rules_map[v["id"]] = edu["rules"]
        db.commit()

    # 2) Post
    post_results = []
    for r in range(req.rounds):
        it = SimIteration(run_id=run.id, round_index=r, status="post"); db.add(it); db.commit()
        post_results += await run_iteration(methods, victims, rules_map, "post_edu", db)

    # 3) 요약
    pre_rate  = sum(1 for x in pre_results if x["outcome"]["is_phished"])/max(1,len(pre_results))
    post_rate = sum(1 for x in post_results if x["outcome"]["is_phished"])/max(1,len(post_results))
    delta_pp = (post_rate - pre_rate) * 100.0

    db.close()
    return RunSummary(run_id=run.id, pre_rate=pre_rate, post_rate=post_rate, delta_pp=delta_pp)
