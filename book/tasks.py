import stripe
from django.conf import settings
from django.utils.datetime_safe import datetime

from book.models import Borrowing, Payment
from book.telegram_bot import notify_overdue_borrowing

from celery import shared_task


@shared_task
def run_sync_with_api() -> None:
    notify_overdue_borrowing(Borrowing.objects.all())


@shared_task
def check_expired_sessions() -> None:
    # Get all Payment objects that are still pending
    pending_payments = Payment.objects.filter(status=Payment.PENDING)

    # Loop through all pending payments and check if the Stripe session has expired
    for payment in pending_payments:
        # Retrieve the Stripe session using the Stripe API
        stripe.api_key = settings.STRIPE_SECRET_KEY
        session = stripe.checkout.Session.retrieve(payment.session_id)

        # Check if the session has expired
        now = datetime.now().timestamp()
        expiration_time = session.created + session.expires_at
        is_expired = expiration_time < now

        # If the session has expired, update the Payment status to EXPIRED
        if is_expired:
            payment.status = Payment.EXPIRED
            payment.save()
