from datetime import date
from typing import List, Dict
from rest_framework import serializers

from .models import Book, Borrowing, Payment
from .telegram_bot import notify_successful_payment


class BookSerializer(serializers.ModelSerializer):
    inventory: int = serializers.SerializerMethodField(read_only=True)

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

    def validate(self, data: Dict) -> Dict:
        if Book.objects.count() >= 1000:
            raise serializers.ValidationError("Maximum number of books reached.")
        return data

    def get_inventory(self, obj: Book) -> int:
        borrowings_count: int = Borrowing.objects.filter(
            actual_return_date=None
        ).count()
        return Book.objects.count() - borrowings_count


class BorrowingSerializer(serializers.ModelSerializer):
    book: int = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())
    user_id: int = serializers.IntegerField(source="user.id", read_only=True)
    user: int = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Borrowing
        fields: List[str] = [
            "id",
            "book",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "user",
            "user_id",
        ]
        read_only_fields: List[str] = ["user"]

    def to_representation(self, instance: Borrowing) -> Dict:
        data: Dict = super().to_representation(instance)
        if (
            self.context["request"].method == "GET"
            and not self.context["request"].user.is_superuser
        ):
            data.pop("user_id", None)
        return data

    def validate(self, data: Dict) -> Dict:
        borrowing_count: int = Borrowing.objects.filter(
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
        fields: List[str] = ("id", "actual_return_date", "book", "user")
        read_only_fields: List[str] = ("id", "book", "user")

    actual_return_date = serializers.SerializerMethodField()

    def get_actual_return_date(self, obj: Borrowing) -> date:
        return obj.actual_return_date


class PaymentSerializer(serializers.ModelSerializer):
    borrowing: int = serializers.PrimaryKeyRelatedField(queryset=Borrowing.objects.all())
    money_to_pay: float = serializers.DecimalField(max_digits=10, decimal_places=2)
    status: str = serializers.ChoiceField(
        choices=Payment.STATUS_CHOICES, default=Payment.PENDING
    )
    type: str = serializers.ChoiceField(
        choices=Payment.TYPE_CHOICES, default=Payment.PAYMENT_TYPE
    )

    def update(self, instance: Payment, validated_data: Dict) -> Payment:
        if validated_data["status"] == Payment.PAID:
            notify_successful_payment(validated_data)
        return super().update(instance, validated_data)

    class Meta:
        model = Payment
        fields: List[str] = [
            "id",
            "borrowing",
            "status",
            "type",
            "session_url",
            "session_id",
            "money_to_pay",
        ]
