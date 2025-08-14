from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.core.config import settings

JUDGE_PROMPT = ChatPromptTemplate.from_template("""
당신은 보이스피싱 판정가입니다.
대화 요약: {dialogue_summary}
수법: {method_name}, 연령대: {age_group}
JSON으로만:
{{"is_phished": true|false, "confidence": 0~1, "rationale": "핵심 근거 1~2줄"}}
""")

def build_judge(llm):
    if settings.USE_STUB_LLM:
        # 스텁일 때는 간단 규칙
        async def _ainvoke(x):
            text = x.get("dialogue_summary","")
            hit = any(k in text for k in ["계좌","이체","원격","링크 클릭"])
            data = {"is_phished": bool(hit), "confidence": 0.7, "rationale": "의심 키워드 탐지" if hit else "방어적 응답"}
            class R: 
                def __init__(self, d): self.__dict__=d
                def __getitem__(self,k): return self.__dict__[k]
            return R(data)
        class C: 
            ainvoke = _ainvoke
        return C()
    return JUDGE_PROMPT | llm | JsonOutputParser()
