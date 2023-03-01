from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.utils import json
from rest_framework.test import APIClient, APITestCase

from book.models import Book, Borrowing, CoverType
from book.serializers import (
    BookSerializer,
    BorrowingSerializer,
)
from customer.models import User


class BookListTestAPI(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpassword",
            is_staff=True,  # set is_staff to True for staff permissions
        )
        self.book1 = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover="Soft",
            daily_fee=9.99,
        )
        self.book2 = Book.objects.create(
            title="Another Test Book",
            author="Another Test Author",
            cover="Hard",
            daily_fee=12.99,
        )

    def test_get_books_unauthenticated(self):
        response = self.client.get(reverse("book:book-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_books_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("book:book-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_book_unauthenticated(self):
        book_data = {"title": "Test Book", "author": "Test Author"}
        response = self.client.post(reverse("book:book-list"), book_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_book_authenticated(self):
        self.client.force_authenticate(user=self.user)
        book_data = {
            "title": "Test Book 2",
            "author": "Test Author 2",
            "cover": "Hard",
            "daily_fee": 14.99,
        }
        response = self.client.post(reverse("book:book-list"), book_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 3)
        self.assertEqual(Book.objects.last().title, "Test Book 2")

    def test_filter_books_by_title(self):
        response = self.client.get(reverse("book:book-list") + "?title=Another")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Another Test Book")


class BookDetailTestAPI(APITestCase):
    def setUp(self):
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover="Hard",
            daily_fee=9.99,
        )
        self.url = reverse("book:book-detail", kwargs={"pk": self.book.id})
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpassword",
            is_staff=True,  # set is_staff to True for staff permissions
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieve_book(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = BookSerializer(self.book)
        self.assertEqual(response.data, serializer.data)

    def test_update_book(self):
        data = {
            "id": self.book.id,
            "title": "New Title",
            "author": "New Author",
            "cover": CoverType.HARD.value,
            "daily_fee": 8.99,
        }
        response = self.client.put(
            self.url, data=json.dumps(data), content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class BorrowingListTestsAPI(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username="testuser1",
            email="testuser1@example.com",
            password="testpassword1",
            is_staff=False,
        )
        self.useradmin = User.objects.create_user(
            username="testuseradmin",
            email="testuseradmin@example.com",
            password="testpasswordadmin",
            is_staff=True,
            is_superuser=True,
        )
        self.user2 = User.objects.create_user(
            username="testuser2",
            email="testuser2@example.com",
            password="testpassword2",
            is_staff=True,
        )

        # Create a book
        self.book1 = Book.objects.create(
            title="Test Book21",
            author="Test Author1",
            cover="Hard",
            daily_fee=5.99,
        )

        self.book2 = Book.objects.create(
            title="Test Book2",
            author="Test Author2",
            cover="Hard",
            daily_fee=2.99,
        )

        # Create a borrowing
        self.borrowing1 = Borrowing.objects.create(
            book=self.book1,
            user=self.user1,
            borrow_date="2022-02-26",
            expected_return_date="2022-03-05",
            actual_return_date=None,
        )

        self.borrowing2 = Borrowing.objects.create(
            book=self.book2,
            user=self.user2,
            borrow_date="2022-02-26",
            expected_return_date="2022-03-05",
            actual_return_date=None,
        )
        self.borrowing3 = Borrowing.objects.create(
            book=self.book2,
            user=self.user1,
            borrow_date="2022-02-26",
            expected_return_date="2022-03-05",
            actual_return_date=None,
        )
        self.url = reverse("book:borrowing-list")

    def test_list_borrowings(self):
        # Authenticate the user
        self.client.force_authenticate(user=self.user1)
        # Make the request
        response = self.client.get(self.url)
        # Check the response status code and data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_borrowings_superuser(self):
        # Authenticate the user
        self.client.force_authenticate(user=self.useradmin)
        # Make the request
        response = self.client.get(self.url)
        # Check the response status code and data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_create_borrowing(self):
        self.client.force_authenticate(user=self.user1)
        data = {
            "book": self.book1.id,
            "borrow_date": "2022-02-26",
            "expected_return_date": "2022-03-05",
            "actual_return_date": None
        }
        response = self.client.post(
            self.url, data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        borrowing = Borrowing.objects.last()
        self.assertEqual(borrowing.book, self.book1)
        self.assertEqual(borrowing.user, self.user1)
        self.assertEqual(str(borrowing.borrow_date), "2022-02-26")
        self.assertEqual(str(borrowing.expected_return_date), "2022-03-05")

    def test_create_borrowing_with_invalid_data(self):
        self.client.force_authenticate(user=self.user1)
        data = {
            "book": self.book1.id,
            "borrow_date": "2023-02-26",
            "actual_return_date": None
        }
        response = self.client.post(
            self.url, data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data, {"expected_return_date": ["This field is required."]}
        )


class BorrowingDetailTestAPI(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpassword",
            is_staff=True,  # set is_staff to True for staff permissions
        )

        # Create a book
        self.book = Book.objects.create(
            title="Test Book2",
            author="Test Author2",
            cover="Hard",
            daily_fee=5.99,
        )

        # Create a borrowing
        self.borrowing = Borrowing.objects.create(
            book=self.book,
            user=self.user,
            borrow_date="2022-02-26",
            expected_return_date="2022-03-05",
            actual_return_date=None,
        )

        # URL for borrowing detail endpoint
        self.url = reverse("book:borrowing-detail", args=[self.borrowing.pk])

    def test_retrieve_borrowing(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        borrowing = Borrowing.objects.get(pk=self.borrowing.pk)
        data = ({
            "id": borrowing.id,
            "book": borrowing.book.id,
            "borrow_date": "2022-02-26",
            "expected_return_date": "2022-03-05",
            "actual_return_date": None
        })
        self.assertEqual(response.data, data)

    def test_update_borrowing(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "book": self.book.pk,
            "borrow_date": "2022-02-27",
            "expected_return_date": "2022-03-05",
            "actual_return_date": None
        }
        response = self.client.put(
            self.url, data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        borrowing = Borrowing.objects.get(pk=self.borrowing.pk)
        self.assertEqual(borrowing.book_id, data["book"])
        self.assertEqual(str(borrowing.borrow_date), data["borrow_date"])
        self.assertEqual(str(borrowing.expected_return_date), data["expected_return_date"])
        self.assertEqual(borrowing.actual_return_date, data["actual_return_date"])

    def test_delete_borrowing(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Borrowing.objects.filter(pk=self.borrowing.pk).exists())


class BorrowingReturnTestAPI(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test_user", email="test_user@example.com", password="password"
        )
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover="Soft",
            daily_fee=9.99,
        )
        self.book1 = Book.objects.create(
            title="Test Book1",
            author="Test Author1",
            cover="Soft",
            daily_fee=5.99,
        )
        self.borrowing = Borrowing.objects.create(
            book=self.book,
            user=self.user,
            borrow_date="2022-02-26",
            expected_return_date=timezone.now().date(),
            actual_return_date=None,
        )
        self.client = APIClient()

    def test_successful_return(self):
        url = reverse("book:borrowing-return", kwargs={"pk": self.borrowing.id})
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.borrowing.refresh_from_db()
        self.assertIsNotNone(self.borrowing.actual_return_date)
        self.assertEqual(self.borrowing.book.inventory, 1)

    def test_return_with_invalid_pk(self):
        url = reverse("book:borrowing-return", kwargs={"pk": 9999})
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_return_twice(self):
        self.borrowing.actual_return_date = timezone.now().date()
        self.borrowing.save()
        url = reverse("book:borrowing-return", kwargs={"pk": self.borrowing.id})
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
