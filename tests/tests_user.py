from django.test import TestCase
from django.contrib.auth import get_user_model


class UserManagerTests(TestCase):
    def test_create_user(self):
        User = get_user_model()
        user = User.objects.create_user(email='test@test.com', password='password')
        self.assertEqual(user.email, 'test@test.com')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='password')

    def test_create_superuser(self):
        User = get_user_model()
        superuser = User.objects.create_superuser(email='superuser@test.com', password='password')
        self.assertEqual(superuser.email, 'superuser@test.com')
        self.assertTrue(superuser.is_active)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

        with self.assertRaises(ValueError):
            User.objects.create_superuser(email='superuser@test.com', password='password', is_superuser=False)

        with self.assertRaises(ValueError):
            User.objects.create_superuser(email='superuser@test.com', password='password', is_staff=False)
