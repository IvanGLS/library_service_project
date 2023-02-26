import stripe
from django.test import TestCase, override_settings
from django.urls import reverse
from customer.models import User
from unittest.mock import patch, Mock
from book.models import Payment, Borrowing, Book
from book.strype_service import create_payment_session


class CreatePaymentSessionTestCase(TestCase):
    @override_settings(STRIPE_SECRET_KEY="test_secret_key")
    @patch("stripe.checkout.Session.create")
    def test_create_payment_session(self, stripe_session_create_mock):
        user = User.objects.create_user(
            username="test_user", email="test_user@example.com", password="password"
        )
        book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover="Soft",
            inventory=1,
            daily_fee=9.99,
        )
        borrowing = Borrowing.objects.create(
            book=book,
            user=user,
            borrow_date="2022-02-26",
            expected_return_date="2022-03-05",
            actual_return_date=None,
        )
        payment = Payment.objects.create(borrowing=borrowing, money_to_pay=10.00)

        mock_session = Mock(
            id="test_session_id",
            url="http://test-session-url.com",
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": int(payment.money_to_pay * 100),
                        "product_data": {
                            "name": payment.borrowing.book.title,
                            "description": "Book borrowing fee",
                        },
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url="http://localhost:8000/success/",
            cancel_url="http://localhost:8000/cancel/",
        )

        def side_effect(*args, **kwargs):
            return mock_session

        stripe_session_create_mock.side_effect = side_effect

        session_id, session_url = create_payment_session(payment)

        self.assertEqual(session_id, "test_session_id")
        self.assertEqual(session_url, "http://test-session-url.com")
        payment.refresh_from_db()
        self.assertEqual(payment.session_id, "test_session_id")
        self.assertEqual(payment.session_url, "http://test-session-url.com")

        # Check that session_id and session_url are present in the response
        response = self.client.get(reverse("book:initiate_payment", args=[payment.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, session_id)
        self.assertContains(response, session_url)

        # Check that payment has the session ID and URL
        payment.refresh_from_db()
        self.assertEqual(payment.session_id, "test_session_id")
        self.assertEqual(payment.session_url, "http://test-session-url.com")
