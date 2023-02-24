from django.utils import timezone
from django.conf import settings

import requests
from django.core.exceptions import ObjectDoesNotExist


def send_telegram_message(message):
    url = (
        f""
        f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/"
        f"sendMessage?chat_id={settings.TELEGRAM_CHAT_ID}&text={message}"
    )
    return requests.get(url).json()  # this sends the message


def notify_borrowing_created(instance):
    message = f"New borrowing created: {instance.user.username} borrowed {instance.book.title}"
    return send_telegram_message(message)


def notify_overdue_borrowing(instance):
    # Check if the borrowing is overdue
    today = timezone.now().date()
    for borrowing in instance:
        if borrowing.expected_return_date < today and not borrowing.actual_return_date:
            # The borrowing is overdue
            try:
                book_title = borrowing.book.title
            except ObjectDoesNotExist:
                book_title = "Unknown book"
            message = (
                f"Overdue borrowing: {borrowing.user.email} "
                f"should have returned {book_title} "
                f"by {borrowing.expected_return_date}"
            )
            send_telegram_message(message)


def notify_successful_payment(instance):
    message = f"Successful payment: {instance.borrowing.user.username} paid {instance.money_to_pay} for {instance.borrowing.book.title}"
    return send_telegram_message(message)
