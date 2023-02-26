from django.db.models import Q, QuerySet
from drf_spectacular.utils import extend_schema, OpenApiParameter
from httpx import Response
from rest_framework import generics
from django.http import JsonResponse

from .models import Book, Borrowing, Payment
from .serializers import BookSerializer, BorrowingSerializer
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

    def get_queryset(self):
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
        borrowing = serializer.save()
        notify_borrowing_created(borrowing)


class BorrowingDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer


def initiate_payment(request, payment_id):
    payment = Payment.objects.get(pk=payment_id)
    session_id, session_url = create_payment_session(payment)
    return JsonResponse({"session_id": session_id, "session_url": session_url})


def payment_success(request):
    return JsonResponse({"message": "Payment successful"})


def payment_cancel(request):
    return JsonResponse({"message": "Payment cancelled"})
