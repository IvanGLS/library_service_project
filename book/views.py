from django.db import transaction
from django.db.models import Q, QuerySet
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics, status, permissions, viewsets, mixins
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import SAFE_METHODS, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Book, Borrowing, Payment
from .serializers import (
    BookSerializer,
    BorrowingSerializer,
    BorrowingReturnSerializer,
    PaymentSerializer,
)
from .strype_service import create_payment_session
from .telegram_bot import notify_borrowing_created


class BookList(generics.ListCreateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Book.objects.all()
        title = self.request.query_params.get("title")
        if title is not None:
            queryset = queryset.filter(title__icontains=title)
        return queryset

    def get_permissions(self):
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
    def get(self, request, *args, **kwargs):
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

    def get_queryset(self) -> QuerySet:
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

    def perform_create(self, serializer):
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
    def put(self, request, *args, **kwargs):
        borrowing = self.get_object()
        borrowing.actual_return_date = timezone.now().date()
        borrowing.book.inventory += 1
        borrowing.book.save()
        borrowing.save()

        # Create payment for the returned borrowing
        payment_data = {
            "borrowing": borrowing.id,
            "status": "Pending",
            "type": "Fine" if borrowing.actual_return_date > borrowing.expected_return_date else "Payment",
            "session_url": "https://example.com/payment",
            "session_id": "abc12"
        }
        # create payment with session url and id
        serializer = PaymentSerializer(data=payment_data)
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()

        payment.save()

        serializer = self.get_serializer(borrowing)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PaymentListView(generics.ListCreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer


class PaymentDetailView(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Get payments only for the authenticated user, or all payments for superuser
        if self.request.user.is_superuser:
            return Payment.objects.all()
        else:
            return Payment.objects.filter(borrowing__user=self.request.user)


payment_detail_view = PaymentDetailView.as_view({"get": "retrieve"})


def initiate_payment(request, payment_id: int) -> JsonResponse:
    payment: Payment = Payment.objects.get(pk=payment_id)
    session_id, session_url = create_payment_session(payment)
    return JsonResponse({"session_id": session_id, "session_url": session_url})


def payment_success(request) -> JsonResponse:
    return JsonResponse({"message": "Payment successful"})


def payment_cancel(request) -> JsonResponse:
    return JsonResponse({"message": "Payment cancelled"})
