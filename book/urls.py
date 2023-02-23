from django.urls import path
from .views import (
    BookList,
    BookDetail,
    BorrowingList,
    BorrowingDetail,
    PaymentList,
    PaymentDetail,
)

urlpatterns = [
    path("books/", BookList.as_view(), name="book-list"),
    path("books/<int:pk>/", BookDetail.as_view(), name="book-detail"),
    path("borrowings/", BorrowingList.as_view(), name="borrowing-list"),
    path("borrowings/<int:pk>/", BorrowingDetail.as_view(), name="borrowing-detail"),
    path("payments/", PaymentList.as_view(), name="payment-list"),
    path("payments/<int:pk>/", PaymentDetail.as_view(), name="payment-detail"),
]


app_name = "book"
