from datetime import timedelta
from unittest.mock import MagicMock, patch
from django.http import JsonResponse
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from book.models import Payment, Book, Borrowing
from book.views import create_payment_session
from customer.models import User


class CreatePaymentSessionTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test_user", email="test_user@example.com", password="password"
        )
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover="Soft",
            daily_fee=9.99,
            inventory=1,
        )
        self.borrowing = Borrowing.objects.create(
            book=self.book,
            user=self.user,
            borrow_date=timezone.now().date(),
            expected_return_date=timezone.now().date() + timedelta(days=7),
            actual_return_date=None,
        )
        self.payment = Payment.objects.create(
            borrowing=self.borrowing,
            money_to_pay=self.book.daily_fee * 7,
            session_id="",
            session_url="",
        )
        self.client = APIClient()

    @patch("stripe.checkout.Session.create")
    def test_create_payment_session(self, mock_create_session: MagicMock):
        session_id = "session_id"
        session_url = "session_url"
        mock_session = MagicMock()
        mock_session.id = session_id
        mock_session.url = session_url
        mock_create_session.return_value = mock_session

        create_payment_session(self.payment)

        self.assertEqual(self.payment.session_id, session_id)
        self.assertEqual(self.payment.session_url, session_url)
        self.assertTrue(mock_create_session.called)
