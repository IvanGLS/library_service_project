from typing import List

from django.utils import timezone
from django.conf import settings

import requests
from django.core.exceptions import ObjectDoesNotExist

from book.models import Payment, Borrowing


def send_telegram_message(message: str) -> dict:
    url = (
        f""
        f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/"
        f"sendMessage?chat_id={settings.TELEGRAM_CHAT_ID}&text={message}"
    )
    return requests.get(url).json()  # this sends the message


def notify_borrowing_created(instance: Borrowing) -> dict:
    message = (
        f"New borrowing created: {instance.user.email} borrowed {instance.book.title}"
    )
    return send_telegram_message(message)


def notify_overdue_borrowing(instance: List[Borrowing]) -> dict:
    today = timezone.now().date()
    overdue_borrowings = []
    for borrowing in instance:
        if borrowing.expected_return_date < today and not borrowing.actual_return_date:
            overdue_borrowings.append(borrowing)

    if overdue_borrowings:
        message = "Overdue borrowings: "
        for borrowing in overdue_borrowings:
            try:
                book_title = borrowing.book.title
            except ObjectDoesNotExist:
                book_title = "Unknown book"
            message += (
                f"{borrowing.user.email} "
                f"should have returned {book_title} "
                f"by {borrowing.expected_return_date}"
            )
        return send_telegram_message(message)
    else:
        return send_telegram_message("No borrowings overdue today!")


def notify_successful_payment(instance: Payment) -> dict:
    message = (
        f"Successful payment: "
        f"{instance.borrowing.user.email} "
        f"paid {instance.money_to_pay} "
        f"for {instance.borrowing.book.title}"
    )
    return send_telegram_message(message)
