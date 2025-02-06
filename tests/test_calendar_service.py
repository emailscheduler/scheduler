import unittest
from unittest.mock import patch, MagicMock
from oauth_utils import get_calendar_service
from calendar_utils import create_calendar_event
from schemas import MeetingDetails

class TestCalendarService(unittest.TestCase):

    @patch('oauth_utils.build')
    def test_get_calendar_service(self, mock_build):
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        service = get_calendar_service()
        self.assertEqual(service, mock_service)

    @patch('oauth_utils.build')
    def test_create_calendar_event(self, mock_build):
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        meeting_details = MeetingDetails(
            summary="Test Meeting",
            agenda="Discuss testing",
            date="2023-10-10",
            start_time="2023-10-10T10:00:00",
            duration=15,
            timezone=None,
            location="Virtual",
            attendees=["test@example.com"]
        )
        create_calendar_event(mock_service, meeting_details)
        mock_service.events().insert.assert_called_once()

if __name__ == '__main__':
    unittest.main() 