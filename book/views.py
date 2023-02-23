from django.db.models import Q
from rest_framework import generics
from .models import Book, Borrowing, Payment
from .serializers import BookSerializer, BorrowingSerializer, PaymentSerializer


class BookList(generics.ListCreateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer


class BookDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer


class BorrowingList(generics.ListCreateAPIView):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer

    def get_queryset(self):
        queryset = Borrowing.objects.all()
        user_id = self.request.query_params.get('user_id')
        is_active = self.request.query_params.get('is_active')

        if user_id:
            queryset = queryset.filter(user_id=user_id)

        if is_active:
            is_active = is_active.lower() == 'true'
            if is_active:
                queryset = queryset.filter(Q(actual_return_date__isnull=True))
            else:
                queryset = queryset.exclude(Q(actual_return_date__isnull=True))

        return queryset


class BorrowingDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer


class PaymentList(generics.ListCreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer


class PaymentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
