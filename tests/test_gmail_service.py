import unittest
import email
import base64
from unittest.mock import patch, MagicMock
from oauth_utils import get_gmail_service
from gmail_utils import mark_email_as_read, send_reply_email, get_email_body, get_unread_emails

class TestGmailService(unittest.TestCase):

    @patch('oauth_utils.build')
    def test_get_gmail_service(self, mock_build):
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        service = get_gmail_service()
        self.assertEqual(service, mock_service)

    @patch('oauth_utils.build')
    def test_mark_email_as_read(self, mock_build):
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mark_email_as_read(mock_service, 'test_id')
        mock_service.users().messages().modify.assert_called_once_with(
            userId="me", id='test_id', body={"removeLabelIds": ["UNREAD"]}
        )

    @patch('gmail_utils.get_email_body')
    @patch('oauth_utils.build')
    def test_get_unread_emails(self, mock_build, mock_get_email_body):
        # Mock the service and its methods
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        # Mock the response from the list method
        mock_service.users().messages().list().execute.return_value = {
            "messages": [{"id": "123"}, {"id": "456"}]
        }

        # Mock the response from the get method for headers
        mock_service.users().messages().get().execute.side_effect = [
            {"payload": {
                "headers": [{"name": "From", "value": "test@example.com"}, {"name": "To", "value": "me@example.com"},
                            {"name": "Subject", "value": "Test Subject"}]}},
            {"raw": "raw_email_body_123"},
            {"payload": {
                "headers": [{"name": "From", "value": "test2@example.com"}, {"name": "To", "value": "me@example.com"},
                            {"name": "Subject", "value": "Test Subject 2"}]}},
            {"raw": "raw_email_body_456"}
        ]

        # Mock the get_email_body function
        mock_get_email_body.side_effect = ["Decoded body 123", "Decoded body 456"]

        # Call the function
        unread_emails = get_unread_emails(mock_service)

        # Assertions
        self.assertEqual(len(unread_emails), 2)
        self.assertEqual(unread_emails[0]['From'], "test@example.com")
        self.assertEqual(unread_emails[0]['Body'], "Decoded body 123")
        self.assertEqual(unread_emails[1]['From'], "test2@example.com")
        self.assertEqual(unread_emails[1]['Body'], "Decoded body 456")

    @patch('oauth_utils.build')
    def test_send_reply_email(self, mock_build):
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        msg_dict = {
            "From": "test_sender@gmail.com",
            "To": "test_recipient@gmail.com",
            "Subject": "Re: test_subject",
            "Message-ID": "test_message_id",
            "Date": "2025-12-25T09:00:00-05:00",
            "Body": "this is a test message",
        }
        reply = "this is a reply"
        send_reply_email(mock_service, msg_dict, reply)
        mock_service.users().messages().send.assert_called_once()


class TestGmailUtils(unittest.TestCase):

    def test_get_email_body_multipart(self):
        # Create a mock multipart email message
        msg = email.message.EmailMessage()
        msg.set_content("This is the plain text part of the email.")
        msg.add_alternative("<html><body>This is the HTML part of the email.</body></html>", subtype='html')

        # Encode the message to base64
        encoded_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('ASCII')

        # Call the function
        body = get_email_body(encoded_message)

        # Assertions
        self.assertEqual(body.strip(), "This is the plain text part of the email.")

    def test_get_email_body_singlepart(self):
        # Create a mock singlepart email message
        msg = email.message.EmailMessage()
        msg.set_content("This is the plain text email.")

        # Encode the message to base64
        encoded_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('ASCII')

        # Call the function
        body = get_email_body(encoded_message)

        # Assertions
        self.assertEqual(body.strip(), "This is the plain text email.")

    def test_get_email_body_no_plain_text(self):
        # Create a mock email message with no plain text
        msg = email.message.EmailMessage()
        msg.add_alternative("<html><body>This is the HTML part of the email.</body></html>", subtype='html')

        # Encode the message to base64
        encoded_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('ASCII')

        # Call the function
        body = get_email_body(encoded_message)

        # Assertions
        self.assertEqual(body, "")

if __name__ == '__main__':
    unittest.main()