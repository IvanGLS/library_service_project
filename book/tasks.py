from book.models import Borrowing
from book.telegram_bot import notify_overdue_borrowing

from celery import shared_task


@shared_task
def run_sync_with_api() -> None:
    notify_overdue_borrowing(Borrowing.objects.all())
