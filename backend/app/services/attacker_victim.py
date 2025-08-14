from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

ATTACKER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "연구용 시뮬레이션 사기범. 수법:{method_name} 전술:{tactics}. 전부 가상, 실PII/실링크 금지."),
    ("human", "{last_victim_utterance}")
])

VICTIM_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "연구용 피해자. 연령대:{age_group} 특성:{traits} 교육규칙:{edu_rules}. 의심시 검색/사이트검증/콜백/신고."),
    ("human", "{attacker_utterance}")
])

def build_attacker(llm, tools):
    llm2 = getattr(llm, "bind_tools", lambda *_: llm)
    llm_with_tools = llm2(tools)
    return ATTACKER_PROMPT | llm_with_tools

def build_victim(llm, tools, memory):
    llm2 = getattr(llm, "bind_tools", lambda *_: llm)
    llm_with_tools = llm2(tools)
    def attach_rules(x): return {**x, "edu_rules": memory.rules_json()}
    return RunnablePassthrough() | RunnableLambda(attach_rules) | VICTIM_PROMPT | llm_with_tools
