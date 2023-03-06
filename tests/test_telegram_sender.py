from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django.conf import settings
from unittest.mock import patch, MagicMock

from book.models import Payment, Borrowing, Book
from book.telegram_bot import (
    notify_successful_payment,
    notify_overdue_borrowing,
    notify_borrowing_created,
    send_telegram_message,
)
from customer.models import User


class UtilsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test_user", email="test_user@example.com", password="password"
        )
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover="Soft",
            inventory=1,
            daily_fee=9.99,
        )
        self.borrowing = Borrowing.objects.create(
            book=self.book,
            user=self.user,
            borrow_date="2022-02-26",
            expected_return_date="2022-03-05",
            actual_return_date=None,
        )
        self.payment = Payment.objects.create(
            borrowing=self.borrowing, money_to_pay=10.00
        )

    @patch("requests.get")
    def test_send_telegram_message(self, mock_requests):
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": True}
        mock_requests.return_value = mock_response
        message = "This is a test message"
        response = send_telegram_message(message)
        mock_requests.assert_called_once_with(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/"
            f"sendMessage?chat_id={settings.TELEGRAM_CHAT_ID}&text={message}"
        )
        self.assertEqual(response, {"ok": True})

    @patch("requests.get")
    def test_notify_borrowing_created(self, mock_requests):
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": True}
        mock_requests.return_value = mock_response
        message = f"New borrowing created: {self.user.email} borrowed {self.book.title}"
        response = notify_borrowing_created(self.borrowing)
        mock_requests.assert_called_once_with(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/"
            f"sendMessage?chat_id={settings.TELEGRAM_CHAT_ID}&text={message}"
        )
        self.assertEqual(response, {"ok": True})

    @patch("requests.get")
    def test_notify_overdue_borrowing(self, mock_requests):
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": True}
        mock_requests.return_value = mock_response
        expected_return_date = timezone.now().date() - timedelta(days=1)
        self.borrowing.expected_return_date = expected_return_date
        self.borrowing.save()
        message = f"Overdue borrowings: {self.user.email} should have returned {self.book.title} by {expected_return_date}"
        notify_overdue_borrowing([self.borrowing])
        mock_requests.assert_called_once_with(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/"
            f"sendMessage?chat_id={settings.TELEGRAM_CHAT_ID}&text={message}"
        )

    @patch("requests.get")
    def test_notify_successful_payment(self, mock_requests):
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": True}
        mock_requests.return_value = mock_response
        message = f"Successful payment: {self.user.email} paid {self.payment.money_to_pay} for {self.book.title}"
        response = notify_successful_payment(self.payment)
        mock_requests.assert_called_once_with(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/"
            f"sendMessage?chat_id={settings.TELEGRAM_CHAT_ID}&text={message}"
        )
        self.assertEqual(response, {"ok": True})
