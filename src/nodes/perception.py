import logging
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from src.state import AgentState

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class ResponseFormat(BaseModel):
    date: str = Field(description="정전 날짜 (YYYY-MM-DD)")
    start: str = Field(description="정전 시작 시간 (반드시 HH:MM 형식으로만 추출, 예: 14:30)")
    end: str = Field(description="정전 종료 시간 (반드시 HH:MM 형식으로만 추출, 예: 14:30)")
    location: str = Field(description="건물명/장소")

model = ChatOllama(model="llama3.2:1b", temperature=0)

def perception_node(state: AgentState):
    print()
    logger.info("--- [Perception Node] 지메일 분석 시작 ---")

    email_data = state.get("email_data", {})
    msg_id = email_data.get("msg_id")
    email_content = email_data.get("email_content", "")

    if not email_content:
        logger.info("❯ 메일 본문 데이터를 확보하지 못했습니다.")
        return {
            "email_data": {"error": "no_email"}, 
            "errors": ["Perception: 메일 수집 실패"],
            "next_step": "error_check"
        }
    
    logger.info(f"❯ 메일 ID: {msg_id} 분석 시작")
    keywords = ["정전", "전력 차단", "전기 점검", "전원 차단"]
    
    if not any(kw in email_content for kw in keywords):
        logger.info(f"❯ [무시] 정전 관련 키워드가 발견되지 않아 작업을 종료합니다.")
        return {
            "email_data": {"status": "ignored_no_keywords"},
            "next_step": "end"
        }

    try:
        logger.info("❯ 정전 관련 키워드 확인됨. LLM 분석을 시작합니다.")
        
        prompt = ChatPromptTemplate.from_template(
    """당신은 정전 공지 분석 전문가입니다. 다음 메일 본문에서 정전 정보를 정확히 추출하세요.

[출력 규칙 - 반드시 지킬 것]
1. 날짜(date)는 반드시 'YYYY-MM-DD' 형식으로만 출력하세요. (예: 2026-01-28)
2. 시간(start, end)은 반드시 'HH:MM' 24시간 형식으로만 출력하세요. (예: 05:00, 22:10)

메일 내용:{content}"""
)
        chain = prompt | model.with_structured_output(ResponseFormat)
        result = chain.invoke({"content": email_content})
        
        extracted_data = result.model_dump()

        if msg_id:
            extracted_data["msg_id"] = msg_id
        
        logger.info(f"❯ 추출 성공: {extracted_data}")
        return {
            "email_data": extracted_data,
            "next_step": "planning"
        }
    except Exception as e:
        logger.error(f"❯ LLM 분석 중 예외 발생: {str(e)}")
        return {
            "email_data": {"error": "extraction_failed"},
            "errors": [f"Perception: LLM 분석 오류 ({str(e)})"],
            "next_step": "error_check"
        }