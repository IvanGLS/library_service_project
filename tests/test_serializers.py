import datetime

from django.test import TestCase
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from book.models import Book, Borrowing
from book.serializers import BookSerializer, BorrowingSerializer

from customer.models import User


class BookSerializerTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="testuser1",
            email="testuser1@example.com",
            password="testpassword1",
            is_staff=False,  # set is_staff to True for staff permissions
        )

    def test_validate_max_books(self):
        # Create 1000 books
        for i in range(1000):
            Book.objects.create(
                title=f"Book {i}",
                author="Test Author2",
                cover="Hard",
                daily_fee=2.99,
            )

        # Test validation error when maximum number of books is reached
        with self.assertRaises(serializers.ValidationError) as cm:
            # Serialize a new book object to trigger the validation error
            data = {
                "title": "New Book",
                "author": "Jane Smith",
                "cover": "Hard",
                "daily_fee": 1.0,
            }
            serializer = BookSerializer(data=data)
            serializer.is_valid(raise_exception=True)

        self.assertEqual(
            str(cm.exception),
            "{'non_field_errors': [ErrorDetail(string='Maximum number of books reached.', code='invalid')]}",
        )

    def test_get_inventory(self):
        # Test that inventory is calculated correctly
        # Create 2 books and 1 borrowing
        book1 = Book.objects.create(
            title="Book 1",
            author="John Doe",
            daily_fee=1.0,
        )
        book2 = Book.objects.create(
            title="Book 2",
            author="Jane Doe",
            daily_fee=2.0,
        )
        book3 = Book.objects.create(
            title="Book 3",
            author="Jim Doe",
            daily_fee=5.0,
        )
        Borrowing.objects.create(
            user=self.user1,
            book=book1,
            borrow_date=datetime.date.today(),
            expected_return_date=datetime.date.today() + datetime.timedelta(days=7),
            actual_return_date=None,
        )
        Borrowing.objects.create(
            user=self.user1,
            book=book2,
            borrow_date=datetime.date.today() - datetime.timedelta(days=7),
            expected_return_date=datetime.date.today(),
            actual_return_date=datetime.date.today(),
        )

        serializer = BookSerializer(instance=[book1, book2, book3], many=True)
        data = serializer.data
        self.assertEqual(data[0]["inventory"], 2)
        self.assertEqual(data[1]["inventory"], 2)
        self.assertEqual(data[2]["inventory"], 2)


class BorrowingSerializerTestCase(TestCase):
    def setUp(self):
        self.book = Book.objects.create(
            title="Book 1",
            author="John Doe",
            daily_fee=1.0,
        )
        self.user = User.objects.create(
            username="testuser",
            password="testpassword",
        )

    def test_validate_max_borrowings(self):
        # Test validation error when maximum number of borrowings for the year is reached
        # Create 50000 borrowings for the current year
        for i in range(50000):
            Borrowing.objects.create(
                book=self.book,
                user=self.user,
                borrow_date=datetime.date.today(),
                expected_return_date=datetime.date.today() + datetime.timedelta(days=7),
            )

        serializer = BorrowingSerializer()
        with self.assertRaises(ValidationError) as cm:
            serializer.validate({})
        self.assertEqual(
            str(cm.exception),
            "[ErrorDetail(string='Maximum number of borrowings reached for this year.', code='invalid')]",
        )
