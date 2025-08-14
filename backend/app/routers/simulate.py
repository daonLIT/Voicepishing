from fastapi import APIRouter
from uuid import uuid4
import json
from backend.app.schemas.simulation import RunRequest, RunSummary
from backend.app.db.base import SessionLocal
from backend.app.db.models import (SimRun, SimIteration, AttackMethod, AgentProfile,
                           PoliceEducation, EducationAssignment, VictimMemory, Outcome)
from backend.app.services.orchestrator import run_iteration
from backend.app.services.med_trainer import med_generate

router = APIRouter()

@router.post("/run", response_model=RunSummary)
async def simulate(req: RunRequest):
    db = SessionLocal()
    try:
        # Run 생성 및 ID 확보
        run = SimRun(id=uuid4(), total_rounds=req.rounds)
        db.add(run); db.commit(); db.refresh(run)
        run_id = run.id  # ✅ 커밋 직후 안전하게 확보

        methods = [
            dict(id=m.id, code=m.code, name=m.name)
            for m in db.query(AttackMethod).filter(AttackMethod.id.in_(req.method_ids)).all()
        ]
        victims = [
            dict(id=v.id, age_group=v.age_group, traits=v.traits)
            for v in db.query(AgentProfile).filter(AgentProfile.id.in_(req.victim_ids)).all()
        ]

        # 1) Pre
        rules_map = {}  # victim_id -> rules
        pre_results = []
        for r in range(req.rounds):
            it = SimIteration(run_id=run_id, round_index=r, status="pre")   # ✅ run_id 사용
            db.add(it); db.commit(); db.refresh(it)
            pre_results += await run_iteration(methods, victims, rules_map, "pre_edu", db, iteration_id=it.id)

        # 실패 근거 텍스트 모음
        fail_reasons = [res["outcome"]["rationale"] for res in pre_results if res["outcome"]["is_phished"]]
        if fail_reasons:
            edu = med_generate("\n".join(fail_reasons))
            # rules 정규화 (str(JSON) -> list[dict])
            rules = edu.get("rules", [])
            if isinstance(rules, str):
                try:
                    rules = json.loads(rules)
                except Exception:
                    rules = []

            edu_row = PoliceEducation(run_id=run_id, title="예방교육 v1",
                                      content_md=edu.get("content_md", ""), rules=rules)
            db.add(edu_row); db.commit(); db.refresh(edu_row)

            for v in victims:
                db.add(EducationAssignment(education_id=edu_row.id, victim_id=v["id"]))
                db.add(VictimMemory(
                    victim_id=v["id"],
                    education_ids=[edu_row.id],
                    keywords=[k for r in rules for k in r.get("keywords", [])]
                ))
                rules_map[v["id"]] = rules  # ✅ 메모리 즉시 반영
            db.commit()

        # 2) Post
        post_results = []
        for r in range(req.rounds):
            it = SimIteration(run_id=run_id, round_index=r, status="post")  # ✅ run_id 사용
            db.add(it); db.commit(); db.refresh(it)
            post_results += await run_iteration(methods, victims, rules_map, "post_edu", db, iteration_id=it.id)

        # 3) 요약
        pre_rate  = sum(1 for x in pre_results if x["outcome"]["is_phished"]) / max(1, len(pre_results))
        post_rate = sum(1 for x in post_results if x["outcome"]["is_phished"]) / max(1, len(post_results))
        delta_pp = (post_rate - pre_rate) * 100.0

        return RunSummary(run_id=run_id, pre_rate=pre_rate, post_rate=post_rate, delta_pp=delta_pp)  # ✅ run_id 사용
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
