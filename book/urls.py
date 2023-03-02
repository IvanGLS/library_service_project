from django.urls import path

from .views import (
    BookList,
    BookDetail,
    BorrowingList,
    BorrowingDetail,
    BorrowingReturn,
    PaymentListView,
    initiate_payment,
    payment_success,
    payment_cancel,
    payment_detail_view,
    payment_expired,
)

urlpatterns = [
    path("books/", BookList.as_view(), name="book-list"),
    path("books/<int:pk>/", BookDetail.as_view(), name="book-detail"),
    path("borrowings/", BorrowingList.as_view(), name="borrowing-list"),
    path("borrowings/<int:pk>/", BorrowingDetail.as_view(), name="borrowing-detail"),
    path(
        "initiate_payment/<int:payment_id>/", initiate_payment, name="initiate_payment"
    ),
    path(
        "borrowings/<int:pk>/return/",
        BorrowingReturn.as_view(),
        name="borrowing-return",
    ),
    path("payments/", PaymentListView.as_view(), name="payments-list"),
    path("payments/<int:pk>/", payment_detail_view, name="payment-detail"),
    path("success/", payment_success, name="payment_success"),
    path("cancel/", payment_cancel, name="payment_cancel"),
    path("expired/", payment_expired, name="payment_expired"),
]


app_name = "book"
