import logging
import argparse
from dateutil import parser
from oauth_utils import get_calendar_service, get_gmail_service
from calendar_utils import create_calendar_event
from gmail_utils import mark_email_as_read, send_reply_email, get_unread_emails
from llm_calls import is_meeting_request, extract_meeting_details, compose_availability_email

# Set up logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_arguments():
    parser = argparse.ArgumentParser(description="Run the email and calendar workflow.")
    parser.add_argument("username", type=str, help="The username to use in the workflow.")
    return parser.parse_args()

def run_workflow(username: str):
    calendar_service = get_calendar_service()
    gmail_service = get_gmail_service()
    logger.info('fetching most recent unread email')
    email_dicts = get_unread_emails(gmail_service)
    logger.info(f'found {len(email_dicts)} emails')
    for email_dict in email_dicts:
        logger.info('reconstructing email...')
        plaintext_email = "\n".join([
            'From: ' + email_dict['From'],
            'To: ' + email_dict['To'],
            # 'Date: ' + email_dict['Date'],
            'Subject: ' + email_dict['Subject'],
            "\n" + email_dict['Body']
        ])
        logger.info('reconstructed email:')
        logger.info(plaintext_email)

        logger.info('determining if email contains meeting...')
        relevant_email = is_meeting_request(plaintext_email)
        if relevant_email.is_meeting_request:
            logger.info(f'meeting contains request')
            logger.info('extracting meeting details...')
            timestamp = parser.parse(email_dict['Date'])
            date_str = timestamp.strftime("%a, %d %b, %Y")
            meeting_details = extract_meeting_details(plaintext_email, username, date_str)
            logger.info('extracted meeting details:')
            logger.info(meeting_details, email_dict)
            if meeting_details.start_time is not None and meeting_details.date is not None:
                logger.info(f'meeting details contain a date and time: {meeting_details.date} {meeting_details.start_time}. creating calendar event...')
                if email_dict['To'] not in meeting_details.attendees: # recipient is attendee
                    meeting_details.attendees.append(email_dict['To'])
                if email_dict['From'] not in meeting_details.attendees: # sender is attendee. note: not always true if secretary scheduling for others
                    meeting_details.attendees.append(email_dict['From'])
                create_calendar_event(calendar_service, meeting_details)
                logger.info('created calendar event')
            else:
                logger.info('meeting details missing date and/or time details. composing followup email...')
                reply_message = compose_availability_email(plaintext_email, username)
                logger.info('response email:')
                logger.info(reply_message)
                logger.info('sending response email...')
                send_reply_email(gmail_service, email_dict, reply_message)
                logger.info('sent_response_email')
        else:
            logger.info("email does not contain meeting request. skipping...")
        logger.info("marking email as read")
        mark_email_as_read(gmail_service, email_dict['Id'])
        logger.info("marked email as read")
        logger.info('====================')
    logger.info('done')
    exit()

if __name__ == "__main__":
    args = parse_arguments()
    run_workflow(args.username)