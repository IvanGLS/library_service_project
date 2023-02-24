from django.db import models
from enum import Enum

from book.telegram_bot import notify_successful_payment
from customer.models import User


class CoverType(Enum):
    HARD = "Hard"
    SOFT = "Soft"


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover = models.CharField(
        choices=[(cover_type.name, cover_type.value) for cover_type in CoverType],
        max_length=4,
    )
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.title


class Borrowing(models.Model):
    borrow_date = models.DateField()
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class Payment(models.Model):
    PENDING = "PENDING"
    PAID = "PAID"
    PAYMENT_TYPE = "PAYMENT"
    FINE_TYPE = "FINE"
    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (PAID, "Paid"),
    ]
    TYPE_CHOICES = [
        (PAYMENT_TYPE, "Payment"),
        (FINE_TYPE, "Fine"),
    ]
    borrowing = models.ForeignKey(Borrowing, on_delete=models.CASCADE)
    status = models.CharField(max_length=7, choices=STATUS_CHOICES, default=PENDING)
    type = models.CharField(max_length=7, choices=TYPE_CHOICES, default=PAYMENT_TYPE)
    session_url = models.URLField()
    session_id = models.CharField(max_length=50)
    money_to_pay = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        if self.status == "PAID":
            notify_successful_payment(self)
        super(Payment, self).save(*args, **kwargs)

    def __str__(self):
        return f"Payment {self.id} ({self.borrowing.book.title})"
