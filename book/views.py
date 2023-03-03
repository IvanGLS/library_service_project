import decimal
from typing import List

import stripe
from django.conf import settings
from django.db import transaction
from django.db.models import Q, QuerySet
from django.http import JsonResponse
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics, status, permissions, viewsets, mixins
from rest_framework.permissions import SAFE_METHODS, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import Book, Borrowing, Payment
from .serializers import (
    BookSerializer,
    BorrowingSerializer,
    BorrowingReturnSerializer,
    PaymentSerializer,
)
from .strype_service import create_payment_session
from .telegram_bot import notify_borrowing_created, notify_successful_payment


class BookList(generics.ListCreateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self) -> QuerySet[Book]:
        queryset = Book.objects.all()
        title = self.request.query_params.get("title")
        if title is not None:
            queryset = queryset.filter(title__icontains=title)
        return queryset

    def get_permissions(self) -> List[permissions.BasePermission]:
        if self.request.method in SAFE_METHODS:
            return [permissions.AllowAny()]
        return [IsAdminUser()]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="title",
                description="Filter by title insensitive contains",
                required=False,
                type=str,
            ),
        ]
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        List of books with filter by title
        """
        return self.list(request, *args, **kwargs)


class BookDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class BorrowingList(generics.ListCreateAPIView):
    queryset = Borrowing.objects.all().select_related("book")
    serializer_class = BorrowingSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs) -> Response:
        book_id = request.data.get("book")
        book = Book.objects.get(id=book_id)
        if book.inventory == 0:
            return Response(
                {"error": "The selected book is not available for borrowing."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Decrement the book's inventory by 1
        book.inventory -= 1
        book.save()

        # Check if the user has any pending payments
        if Payment.objects.filter(
            borrowing__user=request.user, status=Payment.PENDING
        ).exists():
            return Response(
                {
                    "error": "You have pending payments, please pay them before borrowing a new book."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create the borrowing instance
        return super().create(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Borrowing]:
        queryset = super().get_queryset().filter(user=self.request.user)
        user_id = self.request.query_params.get("user_id")
        is_active = self.request.query_params.get("is_active")

        if self.request.user.is_superuser:
            queryset = super().get_queryset().all()
            # If user_id is specified and the user is not a superuser, ignore the filter
            if user_id and not self.request.user.is_superuser:
                user_id = None

        if user_id:
            queryset = queryset.filter(user_id=user_id)

        if is_active:
            is_active = is_active.lower() == "true"
            if is_active:
                queryset = queryset.filter(Q(actual_return_date__isnull=True))
            else:
                queryset = queryset.exclude(Q(actual_return_date__isnull=True))

        return queryset

    def perform_create(self, serializer) -> None:
        borrowing: Borrowing = serializer.save()
        notify_borrowing_created(borrowing)


class BorrowingDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer


class BorrowingReturn(generics.GenericAPIView):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingReturnSerializer
    payment_serializer_class = PaymentSerializer

    @transaction.atomic
    def get(self, request, *args, **kwargs) -> Response:
        borrowing = self.get_object()
        if borrowing.actual_return_date is not None:
            return Response(
                {"error": "Borrowing has already been returned."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        borrowing.actual_return_date = timezone.now().date()
        borrowing.book.inventory += 1
        borrowing.book.save()
        borrowing.save()

        # Create payment for the returned borrowing
        payment_data = {
            "borrowing": borrowing.id,
            "status": "PENDING",
            "type": "FINE"
            if borrowing.actual_return_date > borrowing.expected_return_date
            else "PAYMENT",
            "money_to_pay": self.payment_count(),
        }
        # create payment with session url and id
        serializer = PaymentSerializer(data=payment_data, partial=True)
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()

        # Initiate payment session with Stripe
        initiate_payment(request, payment.id)

        serializer = self.get_serializer(borrowing)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def payment_count(self) -> decimal:
        borrowing = self.get_object()
        book = borrowing.book
        actual_date = borrowing.actual_return_date
        expected_date = borrowing.expected_return_date
        days_borrowed = (expected_date - borrowing.borrow_date).days
        overdue_days = (actual_date - expected_date).days
        money_to_pay = 0

        if overdue_days > 0:
            money_to_pay = (days_borrowed * book.daily_fee) + (
                overdue_days * settings.FINE_MULTIPLIER
            )

        if days_borrowed > 0 and overdue_days == 0:
            money_to_pay = days_borrowed * book.daily_fee

        return money_to_pay


class PaymentListView(generics.ListCreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[Payment]:
        # Get payments only for the authenticated user, or all payments for superuser
        if self.request.user.is_superuser:
            return Payment.objects.all()
        else:
            return Payment.objects.filter(borrowing__user=self.request.user)


class PaymentDetailView(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[Payment]:
        # Get payments only for the authenticated user, or all payments for superuser
        if self.request.user.is_superuser:
            return Payment.objects.all()
        else:
            return Payment.objects.filter(borrowing__user=self.request.user)


payment_detail_view = PaymentDetailView.as_view({"get": "retrieve"})


def initiate_payment(request, payment_id: int) -> JsonResponse:
    payment: Payment = Payment.objects.get(pk=payment_id)
    session_id, session_url = create_payment_session(payment)
    payment.session_id = session_id
    payment.session_url = session_url
    payment.save()
    return JsonResponse({"session_id": session_id, "session_url": session_url})


def payment_success(request) -> JsonResponse:
    session_id = request.GET.get("session_id")
    payment = Payment.objects.get(session_id=session_id)

    stripe.api_key = settings.STRIPE_SECRET_KEY

    # Retrieve the Stripe Checkout Session
    session = stripe.checkout.Session.retrieve(payment.session_id)

    # Check if the payment is successful
    if session.payment_status == "paid":
        payment.status = Payment.PAID
        payment.save()

        # Send payment data via Telegram
        notify_successful_payment(payment)

        return JsonResponse({"message": "Payment successful"})

    else:
        payment.status = session.payment_status
        payment.save()


def payment_cancel(request) -> JsonResponse:
    session_id = request.GET.get("session_id")
    payment = Payment.objects.get(session_id=session_id)

    stripe.api_key = settings.STRIPE_SECRET_KEY

    # Retrieve the Stripe Checkout Session
    session = stripe.checkout.Session.retrieve(payment.session_id)

    # Check if the payment is canceled
    if session.payment_status == "canceled":
        payment.status = Payment.CANCELED
        payment.save()

        return JsonResponse({"message": "Payment cancelled"})

    else:
        payment.status = session.payment_status
        payment.save()
