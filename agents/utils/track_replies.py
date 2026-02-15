from typing import List, Dict, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import pickle
import base64
from email.mime.text import MIMEText
from datetime import datetime
from pydantic import BaseModel
from core.logger import logger

class EmailMessage(BaseModel):
    id: str
    sender: str
    subject: str
    date: datetime
    body: str
    snippet: str

class GmailService:
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    TOKEN_FILE = 'token.pickle'
    CREDENTIALS_FILE = 'credentials.json'
    REDIRECT_PORT = 8000  # Fixed port matching Google Console

    def __init__(self):
        self.creds = None
        self.service = None

    @classmethod
    def get_gmail_service(cls) -> Optional[object]:
        """
        Get authenticated Gmail service
        """
        try:
            creds = None
            
            # Load existing credentials if available
            if os.path.exists(cls.TOKEN_FILE):
                logger.info("Loading existing credentials from token file")
                with open(cls.TOKEN_FILE, 'rb') as token:
                    creds = pickle.load(token)

            # If credentials are not valid, refresh or create new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    logger.info("Refreshing expired credentials")
                    creds.refresh(Request())
                else:
                    logger.info("Getting new credentials")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        cls.CREDENTIALS_FILE, 
                        cls.SCOPES,
                        redirect_uri=f'http://localhost:{cls.REDIRECT_PORT}'  # Explicitly set redirect URI
                    )
                    
                    # Use the specified port
                    creds = flow.run_local_server(
                        port=cls.REDIRECT_PORT,
                        prompt='consent',
                        authorization_prompt_message='Please authorize the application'
                    )

                # Save credentials for future use
                logger.info("Saving credentials to token file")
                with open(cls.TOKEN_FILE, 'wb') as token:
                    pickle.dump(creds, token)

            # Build and return the Gmail service
            logger.info("Building Gmail service")
            service = build('gmail', 'v1', credentials=creds)
            return service

        except Exception as e:
            logger.error(f"Error in Gmail authentication: {str(e)}")
            raise
        
    def authenticate(self) -> None:
        """Handle Gmail API authentication"""
        if os.path.exists(self.TOKEN_FILE):
            with open(self.TOKEN_FILE, 'rb') as token:
                self.creds = pickle.load(token)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.CREDENTIALS_FILE, self.SCOPES)
                self.creds = flow.run_local_server(port=0)

            with open(self.TOKEN_FILE, 'wb') as token:
                pickle.dump(self.creds, token)

        self.service = build('gmail', 'v1', credentials=self.creds)

    def get_messages(self, query: str = None, max_results: int = 10) -> List[EmailMessage]:
        """Fetch messages from Gmail"""
        if not self.service:
            self.authenticate()

        try:
            # Construct the query
            search_query = query if query else "in:inbox"
            
            # Get message list
            results = self.service.users().messages().list(
                userId='me',
                q=search_query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            email_messages = []

            for msg in messages:
                message_data = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()

                # Extract email details
                headers = message_data['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
                sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
                date_str = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
                
                # Get email body
                body = self._get_email_body(message_data['payload'])

                email_msg = EmailMessage(
                    id=msg['id'],
                    sender=sender,
                    subject=subject,
                    date=datetime.strptime(date_str.split(' (')[0].strip(), '%a, %d %b %Y %H:%M:%S %z'),
                    body=body,
                    snippet=message_data.get('snippet', '')
                )
                email_messages.append(email_msg)

            return email_messages

        except Exception as e:
            print(f"Error fetching messages: {str(e)}")
            raise

    def _get_email_body(self, payload: Dict) -> str:
        """Extract email body from the payload"""
        if 'body' in payload and payload['body'].get('data'):
            return base64.urlsafe_b64decode(payload['body']['data']).decode()
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain' and part['body'].get('data'):
                    return base64.urlsafe_b64decode(part['body']['data']).decode()
        
        return ""
    

