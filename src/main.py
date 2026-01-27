import os
import time
import logging
# [추가] 환경 변수를 불러오기 위한 도구
from dotenv import load_dotenv 

# [중요] 다른 import보다 먼저 실행하여 환경 변수를 메모리에 올립니다.
load_dotenv() 

# [수정] 순환 참조 방지를 위해 분리했던 스케줄러를 가져옵니다.
from src.scheduler import scheduler 
from src.graph import graph
from src.tools.gmail_tool import get_latest_shutdown_email

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("agent_log.txt", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

ID_FILE = "processed_ids.txt"

def is_already_processed(msg_id):
    if not os.path.exists(ID_FILE): return False
    with open(ID_FILE, "r") as f:
        return msg_id in f.read().splitlines()

def mark_as_processed(msg_id):
    with open(ID_FILE, "a") as f:
        f.write(msg_id + "\n")

def run_agent():
    print() 
    logger.info("--- [Main] 새로운 메일 스캔 시작 ---")
    
    try:
        msg_id, _ = get_latest_shutdown_email()
        
        if not msg_id or is_already_processed(msg_id):
            logger.info("❯ 처리할 새로운 메일이 없거나 이미 완료되었습니다.")
            return

        logger.info(f"❯ 신규 메일 감지 (ID: {msg_id}). 에이전트 분석 시작.")
        
        initial_state = {
            "email_data": {},
            "errors": [],
            "next_step": ""
        }
        
        final_state = graph.invoke(initial_state)
        
        if not final_state.get("errors"):
            mark_as_processed(msg_id)
            logger.info("❯ 모든 작업이 성공적으로 완료되었습니다.")
        else:
            logger.warning(f"❯ 작업 중단됨. 누적 에러 수: {len(final_state['errors'])}개")
        
    except Exception as e:
        logger.error(f"❯ 에이전트 실행 중 치명적 시스템 오류: {str(e)}")

if __name__ == "__main__":
    logger.info("❯ 에이전트가 가동되었습니다. (10분 주기)")
    
    scheduler.add_job(run_agent, 'interval', minutes=10)
    scheduler.start()

    run_agent()

    try:
        while True: time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("❯ 에이전트가 안전하게 종료되었습니다.")