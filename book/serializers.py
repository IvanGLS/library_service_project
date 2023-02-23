from rest_framework import serializers
from .models import Book, Borrowing, Payment


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = "__all__"


class BorrowingSerializer(serializers.ModelSerializer):
    book = BookSerializer()

    class Meta:
        model = Borrowing
        fields = "__all__"


class PaymentSerializer(serializers.ModelSerializer):
    borrowing = BorrowingSerializer()

    class Meta:
        model = Payment
        fields = "__all__"
