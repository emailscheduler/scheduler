import datetime as dt
import logging
from dateutil import parser
from typing import Any
from schemas import MeetingDetails
from googleapiclient.errors import HttpError
# Set up logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_calendar_event(service: Any, meeting_details: MeetingDetails):
    start_time = parser.parse(meeting_details.date + ' ' + meeting_details.start_time).isoformat()
    if meeting_details.duration is not None:
        end_time = (dt.datetime.fromisoformat(start_time) + dt.timedelta(minutes=meeting_details.duration)).isoformat()
    else: # default 1 hour
        end_time = (dt.datetime.fromisoformat(start_time) + dt.timedelta(minutes=60)).isoformat()
    start = {'dateTime': start_time}
    end = {'dateTime': end_time}
    logger.info(f"start_time: {start_time}, end_time: {end_time}")
    if meeting_details.timezone is not None:
        start['timeZone'] = meeting_details.timezone
        end['timeZone'] = meeting_details.timezone
    else:
        start['timeZone'] = 'America/New_York'
        end['timeZone'] = 'America/New_York'
    if meeting_details.summary is None:
        meeting_details.summary = "Meeting"
    event = {
        'summary': meeting_details.summary,
        'description': meeting_details.agenda,
        'location': meeting_details.location,
        'start': start,
        'end': end,
        'attendees': [{"email": email} for email in meeting_details.attendees]
    }
    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        logger.info(f"Calendar event created: {event.get('htmlLink')}") 
    except HttpError as e:
        logger.error(f"Error creating calendar event: {e}")
        return
