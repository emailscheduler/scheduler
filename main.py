import base64
import email
import os
import re
from openai import OpenAI
import datetime as dt

from dateutil import parser
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
# from googleapiclient.errors import HttpError

from pydantic import BaseModel, Field
from typing import List, Optional

# define the required Google API scopes for OAuth
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]

""" initialize openai api client """
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key = OPENAI_API_KEY)
model = "gpt-4o-mini"

""" pydantic schemas for structured output """
class IsMeetingRequest(BaseModel):
    is_meeting_request: bool = Field(description="Whether the message contains a meeting request")

class MeetingDetails(BaseModel):
    summary: Optional[str] = Field(description="The meeting name, if any")
    agenda: Optional[str] = Field(description="The agenda of the meeting, if any")
    start_time: Optional[str] = Field(description="The date and time of the start of the meeting, if any")
    end_time: Optional[str] = Field(description="The date and time of the end of the meeting, if any")
    location: Optional[str] = Field(description="The location of the meeting, if any")
    timezone: Optional[str] = Field(description="The time zone of the meeting, if any")
    attendees: List[str] = Field(description="List of attendees names and their email addresses")

# class EmailMessage(BaseModel):
#     sender: str = Field(description="The sender of the email")
#     recipient: str = Field(description="The recipient of the email")
#     subject: str = Field(description="The subject of the email")
#     date_time: str = Field(description="The date and time of the email")
#     body: str = Field(description="The body of the email")

""" set up local oauth handshake. delete token.json to reauthenticate if scope changes """
def load_credentials():
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

def get_calendar_service():
    creds = load_credentials()
    service = build("calendar", "v3", credentials=creds)
    return service

def get_gmail_service():
    creds = load_credentials()
    service = build("gmail", "v1", credentials=creds)
    return service

""" google api calls """
def get_email_body(message):
    mime_str = email.message_from_bytes(base64.urlsafe_b64decode(message.encode('ASCII')))

    if mime_str.is_multipart():
        for part in mime_str.walk():
            if part.get_content_type() == 'text/plain':
                body = part.get_payload(decode=True).decode(part.get_content_charset())
                return body
    else:
        if mime_str.get_content_type() == 'text/plain':
            body = mime_str.get_payload(decode=True).decode(mime_str.get_content_charset())
            return body
        else:
            return ""

def get_unread_emails(service):
    results = service.users().messages().list(userId="me", labelIds=["UNREAD"]).execute()
    messages = results.get("messages", [])
    msg_dicts = []
    for message in messages:
        msg_headers = service.users().messages().get(userId="me", id=message['id'], format="metadata").execute()
        msg_body = service.users().messages().get(userId="me", id=message['id'], format="raw").execute()

        msg_dict = {header['name']: header['value'] for header in msg_headers["payload"]["headers"]}
        msg_dict['Body'] = get_email_body(msg_body['raw'])
        msg_dict['Id'] = message['id']
        msg_dicts.append(msg_dict)
    return msg_dicts

def mark_email_as_read(service, id):
    service.users().messages().modify(userId="me", id=id, body={"removeLabelIds": ["UNREAD"]}).execute()
    print(f"Marked email with Message ID: {id} as read.")

def send_reply_email(service, msg_dict, reply):
    message = email.message.EmailMessage() # maybe use pydantic schema

    message['To'] = msg_dict['From']
    message['From'] = msg_dict['To']
    message['Subject'] = "Re: " + re.sub(r'^Re: ', "", msg_dict['Subject'])
    message['In-Reply-To'] = msg_dict['Message-ID']
    message['References'] = msg_dict['Message-ID']
    timestamp = parser.parse(msg_dict['Date'])
    previous_date = timestamp.strftime("%a, %d %b, %Y")
    previous_time = timestamp.strftime("%I:%M %p")

    reply_message = [reply,
                     f"\nOn {previous_date} at {previous_time} {msg_dict['From']} wrote:",
                     "\n".join(['> ' + row for row in msg_dict['Body'].split('\n')])
                    ]

    message.set_content("\n".join(reply_message))

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    create_message = {"raw": encoded_message}
    send_message = service.users().messages().send(userId="me", body=create_message).execute()
    print(f'Sent email with Message ID: {send_message["id"]}')


def create_calendar_event(service, meeting_details: MeetingDetails):
    if meeting_details.end_time is None: # default 1 hour
        meeting_details.end_time = (dt.datetime.fromisoformat(meeting_details.start_time) + dt.timedelta(hours=1)).isoformat()
    if meeting_details.summary is None:
        meeting_details.summary = "Meeting"
    event = {
        'summary': meeting_details.summary,
        'description': meeting_details.agenda,
        'location': meeting_details.location,
        'start': {
            'dateTime': meeting_details.start_time
        },
        'end': {
            'dateTime': meeting_details.end_time
        },
        'attendees': [{"email": email} for email in meeting_details.attendees]
    }

    event = service.events().insert(calendarId='primary', body=event).execute()
    print(f"Calendar event created: {event.get('htmlLink')}")

"""
LLM Calls
"""
def is_meeting_request(text) -> IsMeetingRequest:
    system_message = "Analyze if the email contains a meeting request. Reply with True or False."

    response = client.beta.chat.completions.parse(
        model=model,
        messages=[{"role": "system", "content": system_message},
                  {"role": "user", "content": text}],
        response_format=IsMeetingRequest
    )
    return response.choices[0].message.parsed

def extract_meeting_details(text, recipient) -> MeetingDetails:
    system_message = f"You are a helpful assistant that schedules meetings for {recipient}. Extract meeting information from the email body. Use the email headers as additional context."
    prompt = f"This email contains details about a meeting request. Extract the meeting details.\nEmail:\n{text}"

    response = client.beta.chat.completions.parse(
        model=model,
        messages=[{"role": "system", "content": system_message},
                  {"role": "user", "content": prompt}],
        response_format=MeetingDetails
    )
    return response.choices[0].message.parsed

def compose_availability_email(text, recipient) -> str:
    system_message = f"You are a helpful assistant that responds to emails for {recipient}. Write a response to the following email. Respond with just the body of the email. Do not include headers. Sign the message as {recipient}"
    prompt = f"This email contains details about a meeting request, but is missing some details such as the date and time. Write a response to ask for available times.\n\nEmail:\n{text}"

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system_message},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


""" main function to run workflow """
def run_workflow(recipient_name: str):
    gmail_service = get_gmail_service()
    calendar_service = get_calendar_service()
    print('fetching most recent unread email')
    email_dicts = get_unread_emails(gmail_service)
    print(f'found {len(email_dicts)} emails')
    for email_dict in email_dicts:

        print('reconstructing email...')
        plaintext_email = "\n".join([
            'From: ' + email_dict['From'],
            'To: ' + email_dict['To'],
            'Date: ' + email_dict['Date'],
            'Subject: ' + email_dict['Subject'],
            "\n" + email_dict['Body']
        ])
        print('reconstructed email:')
        print(plaintext_email)

        print('determining if email contains meeting...')
        relevant_email = is_meeting_request(plaintext_email)
        if relevant_email.is_meeting_request: # threshold:
            print(f'meeting contains request')
            print('extracting meeting details...')
            meeting_details = extract_meeting_details(plaintext_email, recipient_name)
            print(meeting_details)
            if meeting_details.start_time is not None:
                print(f'meeting details contain a time: {meeting_details.start_time}. creating calendar event...')
                create_calendar_event(calendar_service, meeting_details)
                print('created calendar event')
            else:
                print('meeting details missing time. composing followup email...')
                reply_message = compose_availability_email(plaintext_email, recipient_name)
                print('response email:')
                print(reply_message)
                print('sending response email...')
                send_reply_email(gmail_service, email_dict, reply_message)
                print('sent_response_email')
        else:
            print("email does not contain meeting request. skipping...")
        print("marking email as read") # don't process email twice. maybe not ideal behavior if user wants to leave it unread
        mark_email_as_read(gmail_service, email_dict['Id'])
        print("marked email as read")
        print('====================')
    print('done')
    exit()

if __name__=="__main__":
    username = "Alan Test"
    run_workflow(username)