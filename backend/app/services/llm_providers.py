from backend.app.core.config import settings
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
import json
import re
import random

# 간단 스텁: 키 없거나 USE_STUB_LLM=True면 규칙적 답변
class Stub:
    def __init__(self, role: str):
        self.role = role

    # 래퍼가 호출하는 동기 API
    def generate(self, text: str) -> str:
        if self.role == "attacker":
            # 매우 단순한 유도 멘트(항상 '링크/인증' 포함 → victim이 방어하도록 유도)
            return "안내드립니다. 금리 인하 혜택 확인을 위해 본인인증이 필요합니다. 링크를 눌러주세요."

        # elif self.role == "victim":
        #     # 키워드 기반 방어 반응
        #     suspicious = any(k in text for k in ["링크", "계좌", "본인인증", "OTP", "원격", "앱 설치", "보안키패드", "빠른 확인"])
        #     if suspicious:
        #         return "의심됩니다. 공식 콜백으로 확인하겠습니다. 링크/원격앱/송금 모두 불가하며 경찰에 신고합니다."
        #     return "추가 안내가 필요합니다. 먼저 공식 홈페이지에서 확인해 보겠습니다."
        elif self.role == "victim":
            suspicious = any(k in text for k in ["링크","계좌","본인인증","OTP","원격","앱 설치","보안키패드","빠른 확인"])
            if suspicious:
                # 30% 확률로 당하게(방어 키워드 없이 수락 멘트 반환)
                if random.random() < 0.30:
                    return "그럼 안내해 주신 링크로 접속해 보겠습니다."
                return "의심됩니다. 공식 콜백으로 확인하겠습니다. 링크/원격앱/송금 모두 불가하며 경찰에 신고합니다."
            return "추가 안내가 필요합니다. 먼저 공식 홈페이지에서 확인해 보겠습니다."

        # else:  # judge
        #     # 매우 단순 판단: 위험 키워드가 있고 거절/콜백/신고가 없으면 피싱 True
        #     risk = any(k in text for k in ["링크", "앱 설치", "원격제어", "계좌", "이체", "본인인증"])
        #     defense = any(k in text for k in ["거절", "콜백", "신고", "불가", "차단", "확인하겠습니다"])
        #     is_phished = bool(risk and not defense)
        #     rationale = "위험 키워드 감지" if is_phished else "방어 반응 확인"
        #     conf = 0.8 if is_phished else 0.7
        #     return json.dumps({"is_phished": is_phished, "confidence": conf, "rationale": rationale}, ensure_ascii=False)
        else:  # judge
            risk = any(k in text for k in ["링크","앱 설치","원격제어","계좌","이체","본인인증"])
            defense = any(k in text for k in ["거절","콜백","신고","불가","차단","확인하겠습니다"])
            is_phished = bool(risk and not defense)
            return json.dumps({"is_phished": is_phished, "confidence": 0.8 if is_phished else 0.7,
                            "rationale": "위험 키워드 감지" if is_phished else "방어 반응 확인"}, ensure_ascii=False)

    # 선택: 동일 로직을 callable로도 제공
    def __call__(self, text: str) -> str:
        return self.generate(text)

    # 기존 비동기 API와도 호환(안 써도 되지만 유지)
    async def ainvoke(self, x):
        # dict가 오면 텍스트로 합침
        if isinstance(x, dict):
            text = "\n".join(f"{k}: {v}" for k, v in x.items())
        else:
            text = str(x)
        class R:
            content: str
        r = R()
        r.content = self.generate(text)
        return r


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
