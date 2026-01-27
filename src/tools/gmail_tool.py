import os.path
import base64
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
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

def get_latest_shutdown_email():
    try:
        service = get_gmail_service()
        search_query = '("정전" OR "전력 차단" OR "전기 점검" OR "전원 차단") -label:SENT -label:DRAFT'
        
        results = service.users().messages().list(userId='me', q=search_query, maxResults=1).execute()
        messages = results.get('messages', [])

        if not messages: 
            return None, None

        msg_id = messages[0]['id']
        msg = service.users().messages().get(userId='me', id=msg_id).execute()
        
        payload = msg['payload']
        body_data = ""

        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    body_data = part['body'].get('data', '')
                    break
        else:
            body_data = payload['body'].get('data', '')

        if not body_data:
            return msg_id, ""

        clean_text = base64.urlsafe_b64decode(body_data).decode('utf-8')
        return msg_id, clean_text 
    
    except Exception as e:
        logger.error(f"Gmail API 통신 오류: {str(e)}")
        return None, None