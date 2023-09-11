import time
from typing import Tuple

import stripe
from django.conf import settings

from book.models import Payment


def create_payment_session(payment: Payment) -> Tuple[str, str]:
    stripe.api_key = settings.STRIPE_SECRET_KEY
    if stripe.api_key:
        amount = int(payment.money_to_pay * 100)
        expiration_time = int(time.time()) + (
            30 * 60
        )  # Set expiration time to 30 minutes from now

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": amount,
                        "product_data": {
                            "name": payment.borrowing.book.title,
                            "description": "Book borrowing fee",
                        },
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url="http://localhost:8000/success/?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="http://localhost:8000/cancel/?session_id={CHECKOUT_SESSION_ID}",
            expires_at=expiration_time,
        )

        payment.session_id = session.id
        payment.session_url = session.url
        payment.save()

        return payment.session_id, payment.session_url

    else:
        raise Exception("Stripe is unavailable, please provide ur Stripe creds")
