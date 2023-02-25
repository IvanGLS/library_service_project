from datetime import date

from rest_framework import serializers
from .models import Book, Borrowing, Payment


class BookSerializer(serializers.ModelSerializer):
    inventory = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Book
        fields = (
            "id",
            "title",
            "author",
            "cover",
            "inventory",
            "daily_fee",
        )

    def validate(self, data):
        if Book.objects.count() >= 1000:
            raise serializers.ValidationError("Maximum number of books reached.")
        return data

    def get_inventory(self, obj):
        borrowings_count = Borrowing.objects.filter(actual_return_date=None).count()
        return Book.objects.count() - borrowings_count


class BorrowingSerializer(serializers.ModelSerializer):
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())

    class Meta:
        model = Borrowing
        fields = "__all__"

    def validate(self, data):
        borrowing_count = Borrowing.objects.filter(
            borrow_date__year=date.today().year
        ).count()
        if borrowing_count >= 50000:
            raise serializers.ValidationError(
                "Maximum number of borrowings reached for this year."
            )
        return data


class PaymentSerializer(serializers.ModelSerializer):
    borrowing = BorrowingSerializer()

    class Meta:
        model = Payment
        fields = "__all__"
