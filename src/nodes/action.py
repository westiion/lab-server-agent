import os
import json
import logging
from src.state import AgentState
from src.tools.ssh_tool import execute_remote_shutdown

logger = logging.getLogger(__name__)

def action_node(state: AgentState):
    print() 
    logger.info("--- [Action Node] 원격 서버 제어 시퀀스 시작 ---")

    email_data = state.get("email_data", {})
    shutdown_time = email_data.get("shutdown_time")
    errors = []

    try:
        servers_json = os.getenv("TARGET_SERVERS", "[]")
        target_servers = json.loads(servers_json)
    except Exception as e:
        errors.append(f"Action: .env의 서버 설정 형식이 잘못되었습니다. ({str(e)})")
        return {"errors": errors, "next_step": "error_check"}

    if not target_servers:
        errors.append("Action: 관리할 서버 목록이 없습니다.")
        return {"errors": errors, "next_step": "error_check"}

    ssh_user = os.getenv("SSH_USER")
    ssh_pw = os.getenv("SSH_PASSWORD")
    success_count = 0

    for server in target_servers:
        logger.info(f"❯ {server['name']}({server['ip']}) 원격 접속 및 명령 전송 시작...")
        
        try:
            success, message = execute_remote_shutdown(
                ip=server['ip'],
                username=ssh_user,
                password=ssh_pw,
                shutdown_time=shutdown_time,
                simulate=True
            )
            
            if success:
                success_count += 1
                logger.info(f"{server['name']} 처리 완료: {message}\n")
            else:
                errors.append(f"Action: {server['name']} 서버 종료 예약 실패 ({message})\n")

        except Exception as e:
            logger.error(f"{server['name']} 시스템 예외: {str(e)}")
            errors.append(f"Action: {server['name']} 치명적 오류 ({str(e)})")

    logger.info(f"--- [Action Node] 제어 시퀀스 종료: {success_count}/{len(target_servers)}대 성공 ---")

    return {
        "errors": errors,
        "next_step": "end" if not errors else "error_check"
    }