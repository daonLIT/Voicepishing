# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.runnables import RunnablePassthrough, RunnableLambda

# # 추가 임포트
# from langchain_core.runnables import RunnableLambda
# from langchain_core.prompt_values import ChatPromptValue
# from langchain_core.messages import AIMessage


# ATTACKER_PROMPT = ChatPromptTemplate.from_messages([
#     ("system", "연구용 시뮬레이션 사기범. 수법:{method_name} 전술:{tactics}. 전부 가상, 실PII/실링크 금지."),
#     ("human", "{last_victim_utterance}")
# ])

# VICTIM_PROMPT = ChatPromptTemplate.from_messages([
#     ("system", "연구용 피해자. 연령대:{age_group} 특성:{traits} 교육규칙:{edu_rules}. 의심시 검색/사이트검증/콜백/신고."),
#     ("human", "{attacker_utterance}")
# ])

# def build_attacker(llm, tools):
#     llm2 = getattr(llm, "bind_tools", lambda *_: llm)
#     llm_with_tools = llm2(tools)
#     return ATTACKER_PROMPT | llm_with_tools

# def build_victim(llm, tools, memory):
#     llm2 = getattr(llm, "bind_tools", lambda *_: llm)
#     llm_with_tools = llm2(tools)
#     def attach_rules(x): return {**x, "edu_rules": memory.rules_json()}
#     return RunnablePassthrough() | RunnableLambda(attach_rules) | VICTIM_PROMPT | llm_with_tools
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.prompt_values import ChatPromptValue
from langchain_core.messages import AIMessage
from typing import Any

# ---- 이미 넣어둔 유틸 그대로 사용 ----
def _normalize_content(c: Any) -> str:
    if c is None:
        return ""
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        parts = []
        for ch in c:
            if isinstance(ch, dict):
                if ch.get("type") == "text" and "text" in ch:
                    parts.append(str(ch["text"]))
                elif "content" in ch:
                    parts.append(str(ch["content"]))
                else:
                    parts.append(str(ch))
            else:
                parts.append(str(ch))
        return "\n".join([p for p in parts if p])
    if isinstance(c, dict):
        try:
            return "\n".join(f"{k}: {v}" for k, v in c.items())
        except Exception:
            return str(c)
    return str(c)

def _promptvalue_to_text(pv: Any) -> str:
    if isinstance(pv, ChatPromptValue):
        texts = []
        for m in pv.messages:
            try:
                texts.append(_normalize_content(m.content))
            except Exception:
                texts.append(str(m))
        return "\n".join([t for t in texts if t])
    if isinstance(pv, dict):
        return "\n".join(f"{k}: {_normalize_content(v)}" for k, v in pv.items())
    return _normalize_content(pv)

def _llm_to_runnable(llm, tools=None):
    if hasattr(llm, "bind_tools"):
        return llm.bind_tools(tools) if tools else llm

    def _call_sync(pv: Any):
        text = _promptvalue_to_text(pv)
        out = llm.generate(text) if hasattr(llm, "generate") else (llm(text) if callable(llm) else str(llm))
        if not isinstance(out, str):
            out = str(out)
        return AIMessage(content=out)

    async def _call_async(pv: Any):
        return _call_sync(pv)

    return RunnableLambda(_call_sync, afunc=_call_async)

# ---- 기존 프롬프트들 ----
ATTACKER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "연구용 시뮬레이션 사기범. 수법:{method_name} 전술:{tactics}. 전부 가상, 실PII/실링크 금지."),
    ("human", "{last_victim_utterance}")
])

VICTIM_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "연구용 피해자. 연령대:{age_group} 특성:{traits} 교육규칙:{edu_rules}. 의심시 검색/사이트검증/콜백/신고."),
    ("human", "{attacker_utterance}")
])

# ---- (새로) 심판자 프롬프트 & 빌더 ----
JUDGE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "너는 판정자다. 아래 정보를 참고해 피싱 여부를 JSON으로만 답하라. 형식: "
               '{{"is_phished": <true|false>, "confidence": <0~1>, "rationale": "<이유>"}}'),
    ("human", "대화요약:\n{dialogue_summary}\n\n수법:{method_name}\n연령대:{age_group}")
])

def build_attacker(llm, tools):
    model = _llm_to_runnable(llm, tools)
    return ATTACKER_PROMPT | model

def build_victim(llm, tools, memory):
    def attach_rules(x):
        return {**x, "edu_rules": memory.rules_json()}
    model = _llm_to_runnable(llm, tools)
    return RunnablePassthrough() | RunnableLambda(attach_rules) | VICTIM_PROMPT | model

def build_judge(llm):
    # 절대 커스텀 객체에 직접 ainvoke 붙이지 마세요(바운드 문제). Runnable 체인으로 통일!
    model = _llm_to_runnable(llm, None)
    return JUDGE_PROMPT | model
