import email
import base64
import logging
import re
from dateutil import parser
from typing import Any, List, Dict
from googleapiclient.errors import HttpError

# Set up logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_unread_emails(service: Any) -> List[Dict[str, str]]:
    try:
        results = service.users().messages().list(userId="me", labelIds=["UNREAD"]).execute()
        messages = results.get("messages", [])
    except HttpError as e:
        logger.error(f"Error getting unread emails: {e}")
        return []

    msg_dicts = []
    for message in messages:
        try:
            msg_headers = service.users().messages().get(userId="me", id=message['id'], format="metadata").execute()
            msg_body = service.users().messages().get(userId="me", id=message['id'], format="raw").execute()

            msg_dict = {header['name']: header['value'] for header in msg_headers["payload"]["headers"]}
            msg_dict['Body'] = get_email_body(msg_body['raw'])
            msg_dict['Id'] = message['id']
            msg_dicts.append(msg_dict)
        except HttpError as e:
            logger.error(f"Error getting email headers or body for message {message['id']}: {e}")
            continue
    return msg_dicts


def get_email_body(encoded_message: Any) -> str:
    try:
        mime_str = email.message_from_bytes(base64.urlsafe_b64decode(encoded_message.encode('ASCII')))
    except (base64.binascii.Error, UnicodeDecodeError) as e:
        logger.error(f"Error decoding email body: {e}")
        return ""

    try:
        if mime_str.is_multipart():
            for part in mime_str.walk():
                if part.get_content_type() == 'text/plain':
                    body = part.get_payload(decode=True).decode(part.get_content_charset())
                    return body
        else:
            if mime_str.get_content_type() == 'text/plain':
                body = mime_str.get_payload(decode=True).decode(mime_str.get_content_charset())
                return body
    except (AttributeError, UnicodeDecodeError) as e:
        logger.error(f"Error getting email body: {e}")
        return ""
    
    return ""

def mark_email_as_read(service: Any, id: str):
    try:
        service.users().messages().modify(userId="me", id=id, body={"removeLabelIds": ["UNREAD"]}).execute()
        logger.info(f"Marked email with Message ID: {id} as read.")
    except HttpError as e:
        logger.error(f"Error marking email with Message ID: {id} as read: {e}")

def send_reply_email(service: Any, msg_dict: Dict[str, str], reply: str):
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

    try:
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    except (UnicodeEncodeError) as e:
        logger.error(f"Error encoding email: {e}")
        return

    try:
        create_message = {"raw": encoded_message}
        send_message = service.users().messages().send(userId="me", body=create_message).execute()
        logger.info(f'Sent email with Message ID: {send_message["id"]}')
    except HttpError as e:
        logger.error(f"Error sending email: {e}")
        return