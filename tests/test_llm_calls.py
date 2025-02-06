import unittest
from unittest.mock import patch, MagicMock
from llm_calls import is_meeting_request, extract_meeting_details, compose_availability_email
from schemas import IsMeetingRequest, MeetingDetails

class TestLLMCalls(unittest.TestCase):

    @patch('llm_calls.client.beta.chat.completions.parse')
    def test_is_meeting_request(self, mock_parse):
        mock_response = MagicMock()
        mock_response.choices[0].message.parsed = IsMeetingRequest(is_meeting_request=True)
        mock_parse.return_value = mock_response
        result = is_meeting_request("Test email content")
        self.assertTrue(result.is_meeting_request)

    @patch('llm_calls.client.beta.chat.completions.parse')
    def test_extract_meeting_details(self, mock_parse):
        mock_response = MagicMock()
        mock_response.choices[0].message.parsed = MeetingDetails(
            summary="Test Meeting",
            date="2023-10-10",
            start_time="10:00:00",
            duration=None,
            timezone=None,
            agenda=None,
            location=None,
            attendees=["test@example.com"]
        )
        date_str = "2023-10-10"
        mock_parse.return_value = mock_response
        result = extract_meeting_details("Test email content", "Recipient", date_str)
        self.assertEqual(result.summary, "Test Meeting")

    @patch('llm_calls.client.chat.completions.create')
    def test_compose_availability_email(self, mock_create):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Please provide your availability."
        mock_create.return_value = mock_response
        result = compose_availability_email("Test email content", "Recipient")
        self.assertEqual(result, "Please provide your availability.")

if __name__ == '__main__':
    unittest.main()