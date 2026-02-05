import time
import logging
import paramiko
from src.scheduler import scheduler 

logger = logging.getLogger(__name__)

def execute_remote_shutdown(ip_port, username, password, shutdown_time, simulate=True):
    if ":" in ip_port:
        ip, port = ip_port.split(':')
        port = int(port)
    else:
        ip, port = ip_port, 22

    time_only = shutdown_time.split(' ')[1] if ' ' in shutdown_time else shutdown_time
    command = command = f"sudo shutdown -h {time_only} '한국 시간 {time_only}에 서버를 종료합니다.'"
    logger.info(f"❯ {ip}:{port} 접속 시도 중... (계정: {username})...")

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh.connect(ip, port=port, username=username, password=password, timeout=5)

        if not simulate:
            stdin, stdout, stderr = ssh.exec_command(command)
            logger.info(f"❯ {ip}:{port} 명령어 전송 완료: '{command}'.")
        else:
            logger.info(f"❯ {ip}:{port} 접속 성공 확인.")
        ssh.close()

        run_date = f"{shutdown_time}:00"
        def final_shutdown_event():
            logger.info(f"{ip}:{port} 서버 전원이 완전히 차단되었습니다.")
        
        scheduler.add_job(final_shutdown_event, 'date', run_date=run_date)
        return True, "Success"

    except Exception as e:
        error_msg = f"{ip_port} 연결 실패: {str(e)}"
        logger.error(f"❯ {error_msg}")
        return False, error_msg