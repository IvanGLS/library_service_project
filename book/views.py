from django.db import transaction
from django.db.models import Q, QuerySet
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from httpx import Response
from rest_framework import generics, status

from .models import Book, Borrowing, Payment
from .serializers import (
    BookSerializer,
    BorrowingSerializer,
    PaymentSerializer,
    BorrowingReturnSerializer,
)
from .strype_service import create_payment_session
from .telegram_bot import notify_borrowing_created


class BookList(generics.ListCreateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    def get_queryset(self) -> QuerySet:
        queryset = Book.objects.all()
        title = self.request.query_params.get("title")
        if title is not None:
            queryset = queryset.filter(title__icontains=title)
        return queryset

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
        """List of books with filter by title"""
        return super().get(request, *args, **kwargs)


class BookDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer


class BorrowingList(generics.ListCreateAPIView):
    queryset = Borrowing.objects.all().select_related("book")
    serializer_class = BorrowingSerializer

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()
        user_id = self.request.query_params.get("user_id")
        is_active = self.request.query_params.get("is_active")

        if user_id:
            queryset = queryset.filter(user_id=user_id)

        if is_active:
            is_active = is_active.lower() == "true"
            if is_active:
                queryset = queryset.filter(Q(actual_return_date__isnull=True))
            else:
                queryset = queryset.exclude(Q(actual_return_date__isnull=True))

        return queryset

    def perform_create(self, serializer):
        borrowing: Borrowing = serializer.save()
        notify_borrowing_created(borrowing)


class PaymentList(generics.ListCreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer


class BorrowingDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer


class BorrowingReturn(generics.GenericAPIView):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingReturnSerializer

    @transaction.atomic
    def put(self, request, pk, *args, **kwargs):
        borrowing = self.get_object()
        borrowing.actual_return_date = timezone.now().date()
        borrowing.book.inventory += 1
        borrowing.book.save()
        borrowing.save()

        serializer = self.get_serializer(borrowing)
        return HttpResponse(serializer.data, status=200)


def initiate_payment(request, payment_id: int) -> JsonResponse:
    payment: Payment = Payment.objects.get(pk=payment_id)
    session_id, session_url = create_payment_session(payment)
    return JsonResponse({"session_id": session_id, "session_url": session_url})


def payment_success(request) -> JsonResponse:
    return JsonResponse({"message": "Payment successful"})


def payment_cancel(request) -> JsonResponse:
    return JsonResponse({"message": "Payment cancelled"})
