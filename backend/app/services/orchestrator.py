import asyncio, datetime, json
from backend.app.core.config import settings
from backend.app.db.models import SimAttempt, Conversation, Outcome
from backend.app.services.llm_providers import attacker_llm, victim_llm, judge_llm
from backend.app.services.attacker_victim import build_attacker, build_victim, build_judge
from backend.app.services.memory import VictimMemory
from backend.app.services.world_tools import darkweb_lookup, sms_broadcast, place_call, open_web, visit_site, report_to_police, policy_check

TOOLS_ATTACKER = [darkweb_lookup, sms_broadcast, place_call]
TOOLS_VICTIM   = [open_web, visit_site, report_to_police, policy_check]

async def run_attempt(method, victim, rules, phase, db, iteration_id):
    llm_a, llm_v, llm_j = attacker_llm(), victim_llm(), judge_llm()
    attacker = build_attacker(llm_a, TOOLS_ATTACKER)
    memory = VictimMemory(victim["id"], rules)
    victim_agent  = build_victim(llm_v, TOOLS_VICTIM, memory)
    judge  = build_judge(llm_j)

    transcript = []
    last_victim = "통화가 시작되었습니다."
    turns = settings.MAX_TURNS

    # DB: attempt
    att = SimAttempt(
        iteration_id= iteration_id,
        method_id=method["id"],
        attacker_id=1,
        victim_id=victim["id"],
        phase=phase
    )
    db.add(att); db.commit(); db.refresh(att)

    for t in range(turns):
        atk = await attacker.ainvoke({
            "method_name": method["name"],
            "tactics": "default",
            "last_victim_utterance": last_victim
        })
        atext = getattr(atk, "content", str(atk))
        transcript.append(("attacker", atext))

        vic = await victim_agent.ainvoke({
            "age_group": victim["age_group"],
            "traits": str(victim.get("traits", "")),
            "attacker_utterance": atext
        })
        vtext = getattr(vic, "content", str(vic))
        transcript.append(("victim", vtext))
        last_victim = vtext

        if any(k in vtext for k in ["콜백", "경찰", "신고", "절대 송금 안 함", "끊겠습니다"]):
            break

    summary = "\n".join([f"{s}: {u[:200]}" for s, u in transcript])

    verdict_msg = await judge.ainvoke({
        "dialogue_summary": summary,
        "method_name": method["name"],
        "age_group": victim["age_group"]
    })

    # ✅ AIMessage → 문자열 → JSON 파싱 (fallback 포함)
    verdict_text = getattr(verdict_msg, "content", str(verdict_msg))
    try:
        verdict = json.loads(verdict_text)
    except Exception:
        verdict = {
            "is_phished": False,
            "confidence": 0.5,
            "rationale": verdict_text[:300]
        }

    # 저장
    conv = Conversation(
        attempt_id=att.id,
        transcript=transcript,
        redacted_transcript=transcript,
        tokens=None,
        cost_usd=None
    )
    db.add(conv)

    out = Outcome(
        attempt_id=att.id,
        is_phished=bool(verdict.get("is_phished")),
        rationale=verdict.get("rationale", ""),
        confidence=float(verdict.get("confidence", 0.5)),
        method_code=(method.get("code") or method["name"]),
        victim_age_group=victim["age_group"]
    )
    db.add(out); db.commit()

    return {
        "attempt_id": att.id,
        "transcript": transcript,
        "outcome": {
            "is_phished": bool(verdict.get("is_phished")),
            "rationale": verdict.get("rationale", ""),
            "confidence": float(verdict.get("confidence", 0.5))
        }
    }

async def run_iteration(methods, victims, rules_map, phase, db, iteration_id):
    results = []
    # 간단히 순차(실운영은 asyncio.gather로 동시성 제어)
    for v in victims:
        for m in methods:
            rules = rules_map.get(v["id"], [])
            res = await run_attempt(m, v, rules, phase, db, iteration_id)
            results.append(res)
    return results
