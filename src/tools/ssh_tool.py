import time
import logging
from datetime import datetime
from src.scheduler import scheduler 

logger = logging.getLogger(__name__)

def execute_remote_shutdown(ip, username, password, shutdown_time, simulate=True):
    command = f"sudo shutdown -h {shutdown_time}"
    logger.info(f"❯ {ip} 접속 시도 중...")
    time.sleep(1)
    logger.info(f"❯ 명령어 전송 예정: '{command}'")

    if simulate:
        logger.info(f"❯ {ip} 응답: 'System shutdown scheduled for {shutdown_time}.'")

        try:
            run_date = f"{shutdown_time}:00"

            def final_shutdown_event():
                logger.info(f"[REAL-TIME EVENT] {ip} 서버 전원이 완전히 차단되었습니다.")

            scheduler.add_job(final_shutdown_event, 'date', run_date=run_date)
            logger.info(f"{shutdown_time}에 서버 종료 예약 완료")

            return True, "Simulation Successful"

        except Exception as e:
            error_msg = f"서버 종료 예약 실패: {str(e)}"
            logger.error(f"{error_msg}")
            return False, error_msg 

    return True, "Success"