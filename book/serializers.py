import typing
from datetime import date

from rest_framework import serializers, status
from rest_framework.generics import get_object_or_404

from .models import Book, Borrowing, Payment
from .telegram_bot import notify_successful_payment


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
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Borrowing
        fields = [
            "id",
            "book",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "user",
            "user_id",
        ]
        read_only_fields = ["user"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if (
            self.context["request"].method == "GET"
            and not self.context["request"].user.is_superuser
        ):
            data.pop("user_id", None)
        return data

    def validate(self, data):
        borrowing_count = Borrowing.objects.filter(
            borrow_date__year=date.today().year
        ).count()
        if borrowing_count >= 50000:
            raise serializers.ValidationError(
                "Maximum number of borrowings reached for this year."
            )
        return data


class BorrowingReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("id", "actual_return_date", "book", "user")
        read_only_fields = ("id", "book", "user")

    actual_return_date = serializers.SerializerMethodField()

    def get_actual_return_date(self, obj):
        return obj.actual_return_date


class CountSerializer(serializers.Serializer):
    days = serializers.IntegerField(required=True)
    book_id = serializers.IntegerField(required=True)


class PaymentSerializer(serializers.ModelSerializer, CountSerializer):
    borrowing = serializers.PrimaryKeyRelatedField(queryset=Borrowing.objects.all())
    money_to_pay = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "borrowing",
            "status",
            "type",
            "session_url",
            "session_id",
            "money_to_pay",
        ]
