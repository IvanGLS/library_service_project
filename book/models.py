from django.db import models
from enum import Enum
from customer.models import User


class CoverType(Enum):
    HARD = "Hard"
    SOFT = "Soft"


class Book(models.Model):
    COVER_CHOICES = [
        (CoverType.SOFT.value, "Soft"),
        (CoverType.HARD.value, "Hard"),
    ]
    cover = models.CharField(choices=COVER_CHOICES, max_length=20)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    inventory = models.PositiveIntegerField(default=0)
    daily_fee = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.title


class Borrowing(models.Model):
    borrow_date = models.DateField()
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=False, blank=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f" borrowing {self.user}, borrowing id {self.id}"


class Payment(models.Model):
    PENDING = "PENDING"
    PAID = "PAID"
    CANCELED = "CANCELED"
    EXPIRED = "EXPIRED"
    PAYMENT_TYPE = "PAYMENT"
    FINE_TYPE = "FINE"
    STATUS_CHOICES = [
        (CANCELED, "Canceled"),
        (PENDING, "Pending"),
        (PAID, "Paid"),
        (EXPIRED, "Expired"),
    ]
    TYPE_CHOICES = [
        (PAYMENT_TYPE, "Payment"),
        (FINE_TYPE, "Fine"),
    ]
    borrowing = models.ForeignKey(Borrowing, on_delete=models.CASCADE)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default=PENDING)
    type = models.CharField(max_length=8, choices=TYPE_CHOICES, default=PAYMENT_TYPE)
    session_url = models.URLField(max_length=400)
    session_id = models.CharField(max_length=400)
    money_to_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Payment {self.id} ({self.borrowing.book.title})"
