from pydantic import BaseModel, Field
from typing import List, Optional

class IsMeetingRequest(BaseModel):
    is_meeting_request: bool = Field(description="Whether the message contains a meeting request")

class MeetingDetails(BaseModel):
    summary: Optional[str] = Field(description="The meeting name, if any")
    agenda: Optional[str] = Field(description="The agenda of the meeting, if any")
    date: Optional[str] = Field(description="The date of the meeting, if any")
    start_time: Optional[str] = Field(description="The time of the meeting, if any")
    duration: Optional[int] = Field(description="The length of the meeting in minutes, if any")
    location: Optional[str] = Field(description="The location of the meeting, if any")
    timezone: Optional[str] = Field(description="The time zone of the meeting, if any")
    attendees: List[str] = Field(description="List of attendees names and their email addresses")

class EmailMessage(BaseModel):
    sender: str = Field(description="The sender of the email")
    recipient: str = Field(description="The recipient of the email")
    subject: str = Field(description="The subject of the email")
    body: str = Field(description="The body of the email")
