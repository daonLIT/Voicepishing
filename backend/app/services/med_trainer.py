from app.core.config import settings
from app.services.llm_providers import judge_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

MED_PROMPT = ChatPromptTemplate.from_template("""
실패사례 요약:
{fail_summaries}
연령/수법 공통 위험 신호를 뽑아 교육자료와 규칙을 만들어주세요.
JSON만:
{{"content_md":"...", "rules":[{{"name":"...", "keywords":["...","..."]}}]}}
""")

def med_generate(fail_summaries: str):
    # 스텁: 간단 키워드 규칙
    if settings.USE_STUB_LLM:
        return {
          "content_md": "# 예방법\n- 링크/앱 설치 요구시 절대 응하지 마세요\n- 콜백으로 기관 대표번호 확인\n- 가족/기관 사칭은 영상통화나 공식앱으로 재확인",
          "rules": [
            {"name":"긴급송금압박","keywords":["긴급","오늘안에","당장","구속"]},
            {"name":"링크유도","keywords":["링크","URL","업데이트"]},
            {"name":"원격앱","keywords":["원격","앱 설치","접속"]}
          ]
        }
    llm = judge_llm()  # 간단히 동일 LLM 사용
    parser = JsonOutputParser()
    chain = MED_PROMPT | llm | parser
    # 동기식 인터페이스 보장 위해 ainvoke 대신 invoke 사용
    res = chain.invoke({"fail_summaries": fail_summaries})
    return res
