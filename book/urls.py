from django.urls import path
from .views import (
    BookList,
    BookDetail,
    BorrowingList,
    BorrowingDetail,
)

urlpatterns = [
    path("books/", BookList.as_view(), name="book-list"),
    path("books/<int:pk>/", BookDetail.as_view(), name="book-detail"),
    path("borrowings/", BorrowingList.as_view(), name="borrowing-list"),
    path("borrowings/<int:pk>/", BorrowingDetail.as_view(), name="borrowing-detail"),
]


app_name = "book"
