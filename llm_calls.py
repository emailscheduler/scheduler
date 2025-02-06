from openai import OpenAI
import os
import logging
from schemas import IsMeetingRequest, MeetingDetails

# Set up logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI API client
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)
model = "gpt-4o-mini"

def is_meeting_request(text: str) -> IsMeetingRequest:
    system_message = "Analyze if the email contains a meeting request. Reply with True or False."

    response = client.beta.chat.completions.parse(
        model=model,
        messages=[{"role": "system", "content": system_message},
                  {"role": "user", "content": text}],
        response_format=IsMeetingRequest
    )
    logger.info("Checked if email contains a meeting request.")
    return response.choices[0].message.parsed

def extract_meeting_details(text: str, username: str, date: str) -> MeetingDetails:
    system_message = f"You are a helpful assistant that schedules meetings for {username}. Extract meeting details from the following email. This email was sent on {date}. Date and time details, if found, should be relative to {date}."
    prompt = f'Email:\n"{text}"'

    response = client.beta.chat.completions.parse(
        model=model,
        messages=[{"role": "system", "content": system_message},
                  {"role": "user", "content": prompt}],
        response_format=MeetingDetails
    )
    logger.info("Extracted meeting details from email.")
    return response.choices[0].message.parsed

def compose_availability_email(text: str, username: str) -> str:
    system_message = f"You are a helpful assistant that responds to emails for {username}. Write a response to the following email. Respond with just the body of the email. Do not include headers. Sign the message as {username}"
    prompt = f"This email contains details about a meeting request, but is missing some details such as the date and time. Write a response to ask for available times.\n\nEmail:\n{text}"

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system_message},
                  {"role": "user", "content": prompt}]
    )
    logger.info("Composed availability email.")
    return response.choices[0].message.content