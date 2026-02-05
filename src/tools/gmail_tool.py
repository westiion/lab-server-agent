import os.path
import base64
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service(): # 구글 서버로부터 인증된 서비스 객체를 빌드
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

def get_unprocessed_shutdown_emails(processed_ids: set): # 처리되지 않은 모든 메일 가져오기
    try:
        service = get_gmail_service()
        search_query = '("정전" OR "전력 차단" OR "전기 점검" OR "전원 차단" OR "안전 점검" OR "전기 공급 차단" OR "단전") -label:SENT -label:DRAFT'
        
        results = service.users().messages().list(userId='me', q=search_query, maxResults=5).execute()
        messages = results.get('messages', [])

        if not messages: 
            return []

        unprocessed_emails = []
        
        for msg_item in messages:
            msg_id = msg_item['id']
            
            if msg_id in processed_ids:
                continue
            
            try:
                msg = service.users().messages().get(userId='me', id=msg_id).execute()
                internal_date = int(msg.get('internalDate', 0))
                
                payload = msg['payload']
                body_data = ""

                if 'parts' in payload:
                    for part in payload['parts']:
                        if part['mimeType'] == 'text/plain':
                            body_data = part['body'].get('data', '')
                            break
                else:
                    body_data = payload['body'].get('data', '')

                clean_text = ""
                if body_data:
                    clean_text = base64.urlsafe_b64decode(body_data).decode('utf-8')
                
                unprocessed_emails.append((msg_id, clean_text, internal_date))
                
            except Exception as e:
                logger.warning(f"메일 ID {msg_id} 처리 중 오류: {str(e)}")
                continue
    
        unprocessed_emails.sort(key=lambda x: x[2])
        
        return [(msg_id, body) for msg_id, body, _ in unprocessed_emails]
    
    except Exception as e:
        logger.error(f"Gmail API 통신 오류: {str(e)}")
        return []