# backend/app/services/world_tools.py
from langchain_core.tools import tool
import json, random, re

def _fake_id() -> str:
    """모의 통화 ID를 생성한다."""
    return f"sim-{random.randint(100000,999999)}"

def _parse_segment_count(segment: str) -> int:
    """세그먼트 문자열에서 전송 대상 수를 파싱한다. 예: 'random:50' -> 50. 실패 시 50."""
    m = re.match(r"random:(\d+)", segment or "")
    return int(m.group(1)) if m else 50

@tool("darkweb_lookup")
def darkweb_lookup(query: str) -> str:
    """[공격자용] 다크웹에서 키워드(query)를 모의 검색해 유출 의심 정보를 반환한다.
    Args:
        query: 검색 키워드(이름/전화 일부 등). 실제 검색 아님(모의).
    Returns:
        JSON 문자열: {"simulated": true, "hits": [{"name":..., "phone":..., "leak":...}, ...]}
    """
    data = {"simulated": True, "hits": [
        {"name": "김OO", "phone": "010-9XX6-1XX3", "leak": "메신저 탈취 의심"},
        {"name": "이OO", "phone": "010-7XX2-5XX1", "leak": "택배 스미싱 대상"}
    ]}
    return json.dumps(data, ensure_ascii=False)

@tool("sms_broadcast")
def sms_broadcast(message: str, segment: str = "random:50") -> str:
    """[공격자용] 지정 세그먼트(예: random:50)에 메시지를 일괄 발송하는 모의 툴.
    Args:
        message: 전송할 문자 내용(모의).
        segment: 대상 세그먼트. 'random:<N>' 형식일 경우 N명으로 간주.
    Returns:
        JSON 문자열: {"simulated": true, "sent": <int>, "segment": "<원본세그먼트>"}
    """
    sent = _parse_segment_count(segment)
    return json.dumps({"simulated": True, "sent": sent, "segment": segment}, ensure_ascii=False)

@tool("place_call")
def place_call(target_id: str, script: str) -> str:
    """[공격자용] 특정 대상에게 전화를 연결하는 모의 툴.
    Args:
        target_id: 대상 식별자(모의 ID).
        script: 통화 스크립트/대본.
    Returns:
        JSON 문자열: {"simulated": true, "call_id": "sim-XXXXXX", "target_id": "<id>"}
    """
    return json.dumps({"simulated": True, "call_id": _fake_id(), "target_id": target_id}, ensure_ascii=False)

@tool("open_web")
def open_web(query: str) -> str:
    """[피해자용] 공개 웹 검색을 모의 수행해 관련 결과 목록을 반환한다.
    Args:
        query: 검색어(모의).
    Returns:
        JSON 문자열: {"simulated": true, "results": [{"url":..., "snippet":...}, ...]}
    """
    results = [
        {"url": "https://bank-help.sim/verify", "snippet": "공식 확인 절차"},
        {"url": "https://pay-secure.sim/update", "snippet": "보안 업데이트(의심)"}
    ]
    return json.dumps({"simulated": True, "results": results}, ensure_ascii=False)

@tool("visit_site")
def visit_site(url: str) -> str:
    """[피해자용] URL 페이지 접속을 모의 수행하고 간단한 위험 신호를 반환한다.
    Args:
        url: 접속하려는 주소(모의).
    Returns:
        JSON 문자열: {"url": "...", "title": "...", "risk_tags": [...], "simulated": true}
    """
    page = {
        "url": url,
        "title": "보안 업데이트",
        "risk_tags": ["typo-domain", "https-mismatch"],
        "simulated": True,
    }
    return json.dumps(page, ensure_ascii=False)

@tool("report_to_police")
def report_to_police(citizen_id: str, evidence: str) -> str:
    """[피해자용] 모의 신고를 접수 큐에 적재한다.
    Args:
        citizen_id: 신고자/피해자 식별자(모의).
        evidence: 신고 근거(대화 요약, 링크 등).
    Returns:
        JSON 문자열: {"ok": true, "queued": true, "simulated": true}
    """
    return json.dumps({"ok": True, "queued": True, "simulated": True}, ensure_ascii=False)

@tool("policy_check")
def policy_check(user_utterance: str, rules_json: str = "[]") -> str:
    """[피해자용] 교육 규칙(rules_json)의 키워드와 사용자 발화를 비교해 위반/트리거를 판단한다.
    Args:
        user_utterance: 사용자의 최신 발화(피싱 유도 문구 포함 가능).
        rules_json: JSON 문자열. 예: [{"name":"링크유도","keywords":["링크","URL","업데이트"]}, ...]
    Returns:
        문자열: "violation=true|false; triggered=[...]"  (단순 파싱 가능한 포맷)
    """
    import json as _json
    try:
        rules = _json.loads(rules_json) if rules_json else []
    except Exception:
        rules = []
    triggers = [r.get("name", "") for r in rules if any(k in user_utterance for k in r.get("keywords", []))]
    return f"violation={'true' if triggers else 'false'}; triggered={triggers}"
