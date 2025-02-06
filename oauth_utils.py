import logging
import os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError

from typing import Any

# Set up logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]

def load_credentials() -> Any:
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds

def get_calendar_service() -> Any:
    try:
        creds = load_credentials()
        service = build("calendar", "v3", credentials=creds)
        return service
    except HttpError as e:
        logger.error(f"Error getting calendar service: {e}")
        return None
    
    

def get_gmail_service() -> Any:
    try:
        creds = load_credentials()
        service = build("gmail", "v1", credentials=creds)
        return service
    except HttpError as e:
        logger.error(f"Error getting gmail service: {e}")
        return None
