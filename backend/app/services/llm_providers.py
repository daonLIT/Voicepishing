from app.core.config import settings
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

# 간단 스텁: 키 없거나 USE_STUB_LLM=True면 규칙적 답변
class Stub:
    def __init__(self, role): self.role = role
    async def ainvoke(self, x):
        # 매우 단순한 규칙 응답
        if self.role=="attacker":
            msg = f"[모의사기:{x.get('method_name')}] 빠른 확인이 필요합니다. 링크 클릭 또는 계좌 확인을 요구합니다."
        elif self.role=="victim":
            text = x.get("attacker_utterance","")
            if any(k in text for k in ["링크","계좌","빠른","본인인증"]):
                msg = "의심됩니다. 콜백 후 확인하겠습니다. 링크/송금 불가."
            else:
                msg = "무슨 일인지 추가 확인이 필요합니다."
        else:  # judge
            # 공격 키워드 있으면 피해 True 확률 높임(데모)
            msg = '{"is_phished": false, "confidence": 0.7, "rationale":"방어 반응"}'
        class R: content = msg
        return R

def attacker_llm():
    if settings.USE_STUB_LLM or not settings.OPENAI_API_KEY:
        return Stub("attacker")
    return ChatOpenAI(model=settings.OPENAI_MODEL, temperature=0.8, api_key=settings.OPENAI_API_KEY)

def victim_llm():
    if settings.USE_STUB_LLM or not settings.GEMINI_API_KEY:
        return Stub("victim")
    return ChatGoogleGenerativeAI(model=settings.GEMINI_MODEL, temperature=0.7, google_api_key=settings.GEMINI_API_KEY)

def judge_llm():
    if settings.USE_STUB_LLM or not settings.OPENAI_API_KEY:
        return Stub("judge")
    return ChatOpenAI(model=settings.OPENAI_MODEL, temperature=0.2, api_key=settings.OPENAI_API_KEY)
