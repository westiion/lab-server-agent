import os
import logging
from datetime import datetime, timedelta
from src.state import AgentState

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def planning_node(state: AgentState):
    print()
    logger.info("--- [Planning Node] 종료 계획 수립 시작 ---")
    
    email_data = state.get("email_data", {})
    target_location = email_data.get("location", "")
    my_location = os.getenv("MY_SERVER_LOCATION")
    target_date = email_data.get("date")
    start_time_str = email_data.get("start")
    errors = []

    if not my_location:
        errors.append("환경 변수 'MY_SERVER_LOCATION'이 설정되지 않았습니다.")
        return {"errors": errors, "next_step": "error_check"}
    
    if my_location not in target_location:
        logger.info(f"❯ 정전 지역({target_location})에 내 위치({my_location})가 포함되지 않아 작업을 종료합니다.")
        return {"next_step": "end"}
    
    if not target_date or not start_time_str:
        errors.append("Planning: 필수 정전 정보가 누락되어 계획을 수립할 수 없습니다.")
        return {"errors": errors, "next_step": "error_check"}
    
    try:
        current_time = datetime.now()
        
        if 'T' in start_time_str:
            clean_iso = start_time_str.replace('Z', '').split('.')[0]
            outage_time = datetime.fromisoformat(clean_iso)
        else:
            outage_time = datetime.strptime(f"{target_date} {start_time_str}", "%Y-%m-%d %H:%M")
        
        recommended_shutdown = outage_time - timedelta(minutes=30)
        
        if current_time >= outage_time:
            logger.warning(f"❯ [상황 1] 이미 정전 시각({outage_time.strftime('%H:%M')})이 경과하여 자동 종료가 불가합니다.")
            errors.append("Planning: 현재 시각이 정전 예정 시각보다 늦습니다.")
            return {"errors": errors, "next_step": "error_check"}

        elif current_time >= recommended_shutdown:
            logger.warning(f"❯ [상황 2] 권장 종료 시간({recommended_shutdown.strftime('%Y-%m-%d %H:%M')})이 경과했습니다.")
            shutdown_time_dt = current_time + timedelta(minutes=1)
            logger.info(f"❯ 즉시 종료 절차 개시 (예약 시각: {shutdown_time_dt.strftime('%Y-%m-%d %H:%M')})")

        else:
            shutdown_time_dt = recommended_shutdown
            logger.info(f"❯ [상황 3] 정상 예약: {shutdown_time_dt.strftime('%Y-%m-%d %H:%M')}에 종료를 예약합니다.")

        shutdown_time_str = shutdown_time_dt.strftime("%Y-%m-%d %H:%M")
        updated_email_data = email_data.copy()
        updated_email_data["shutdown_time"] = shutdown_time_str
        
        return {
            "email_data": updated_email_data,
            "errors": errors,
            "next_step": "action"
        }
        
    except Exception as e:
        logger.error(f"❯ 시간 데이터 분석 중 예외 발생: {str(e)}")
        errors.append(f"Planning: 시간 계산 중 시스템 오류 (사유: {str(e)})")
        return {"errors": errors, "next_step": "error_check"}