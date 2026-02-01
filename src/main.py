import os
import time
import logging
from dotenv import load_dotenv 

load_dotenv() 

from src.scheduler import scheduler 
from src.graph import graph
from src.tools.gmail_tool import get_unprocessed_shutdown_emails

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

def get_processed_ids():
    if not os.path.exists(ID_FILE):
        return set()
    with open(ID_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def mark_as_processed(msg_id):
    with open(ID_FILE, "a") as f:
        f.write(msg_id + "\n")

def run_agent():
    print() 
    logger.info("--- [Main] 새로운 메일 스캔 시작 ---")
    
    try:
        processed_ids = get_processed_ids()
        unprocessed_emails = get_unprocessed_shutdown_emails(processed_ids)
        
        if not unprocessed_emails:
            logger.info("❯ 처리할 새로운 메일이 없습니다.")
            return
        
        logger.info(f"❯ 미처리 메일 {len(unprocessed_emails)}개 발견. 순차 처리 시작.")
        
        # 각 메일마다 독립적으로 그래프 실행
        for idx, (msg_id, email_content) in enumerate(unprocessed_emails, 1):
            logger.info(f"--- [메일 {idx}/{len(unprocessed_emails)}] ID: {msg_id} 처리 시작 ---")
            
            try:
                initial_state = {
                    "email_data": {
                        "msg_id": msg_id,
                        "email_content": email_content
                    },
                    "errors": [],
                    "next_step": ""
                }
                
                final_state = graph.invoke(initial_state)
                
                if not final_state.get("errors"):
                    mark_as_processed(msg_id)
                    logger.info(f"❯ 메일 {idx}/{len(unprocessed_emails)} (ID: {msg_id}) 처리 완료.")
                else:
                    logger.warning(f"❯ 메일 {idx}/{len(unprocessed_emails)} (ID: {msg_id}) 처리 중 오류 발생. 누적 에러 수: {len(final_state['errors'])}개")
                    
            except Exception as e:
                logger.error(f"❯ 메일 {idx}/{len(unprocessed_emails)} (ID: {msg_id}) 처리 중 예외 발생: {str(e)}")
                continue
        
        logger.info("--- [Main] 모든 메일 처리 완료 ---")
        
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