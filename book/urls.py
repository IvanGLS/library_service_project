from django.urls import path
from .views import (
    BookList,
    BookDetail,
    BorrowingList,
    BorrowingDetail,
    initiate_payment,
    payment_success,
    payment_cancel,
)

urlpatterns = [
    path("books/", BookList.as_view(), name="book-list"),
    path("books/<int:pk>/", BookDetail.as_view(), name="book-detail"),
    path("borrowings/", BorrowingList.as_view(), name="borrowing-list"),
    path("borrowings/<int:pk>/", BorrowingDetail.as_view(), name="borrowing-detail"),
    path(
        "initiate_payment/<int:payment_id>/", initiate_payment, name="initiate_payment"
    ),
    path("success/", payment_success, name="payment_success"),
    path("cancel/", payment_cancel, name="payment_cancel"),
]


app_name = "book"
