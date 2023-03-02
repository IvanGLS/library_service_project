import stripe
from django.conf import settings
from django.http import JsonResponse

from book.models import Payment


def create_payment_session(payment: Payment) -> JsonResponse:
    stripe.api_key = settings.STRIPE_SECRET_KEY

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "unit_amount": (payment.money_to_pay * 100),
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

    payment.session_id = session.id
    payment.session_url = session.url
    payment.save()
    return JsonResponse({"session_id": session.id, "session_url": session.url})
