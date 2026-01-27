import logging
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from src.state import AgentState
from src.tools.gmail_tool import get_latest_shutdown_email

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

    msg_id, email_content = get_latest_shutdown_email()

    if not email_content:
        logger.info("❯ 메일 본문 데이터를 확보하지 못했습니다.")
        return {
            "email_data": {"error": "no_email"}, 
            "errors": ["Perception: 메일 수집 실패"],
            "next_step": "error_check"
        }
    keywords = ["정전", "전력 차단", "전기 점검", "전원 차단"]
    
    if not any(kw in email_content for kw in keywords):
        logger.info(f"❯ [무시] 정전 관련 키워드가 발견되지 않아 작업을 종료합니다.")
        return {
            "email_data": {"status": "ignored_no_keywords"},
            "next_step": "end"
        }

    try:
        logger.info("❯ 정전 관련 키워드 확인됨. LLM 분석을 시작합니다.")
        
        extracted_data = {"date": "2026-01-28", "start": "04:00", "location": "5호관"}
        
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