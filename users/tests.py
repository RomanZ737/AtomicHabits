# users/tests.py
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import CustomUser
from users.serializers import CustomUserSerializer


class TestCustomUserModel(TestCase):
    """Тесты модели CustomUser."""

    def test_create_user(self):
        user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            phone_number='+79991234567',
            city='Москва',
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertIsNone(user.telegram_chat_id)

    def test_create_user_without_email_raises_error(self):
        with self.assertRaises(ValueError):
            CustomUser.objects.create_user(email='', password='pass')

    def test_create_superuser(self):
        admin = CustomUser.objects.create_superuser(
            email='admin@example.com',
            password='adminpass',
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)

    def test_str_returns_email(self):
        user = CustomUser(email='str@example.com')
        self.assertEqual(str(user), 'str@example.com')


class TestCustomUserSerializer(TestCase):
    """Тесты сериализатора пользователя."""

    def test_create_user_via_serializer(self):
        data = {
            'email': 'new@example.com',
            'password': 'securepass',
            'phone_number': '+79990001122',
            'city': 'СПб',
        }
        serializer = CustomUserSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.email, 'new@example.com')
        self.assertTrue(user.check_password('securepass'))

    def test_create_with_invalid_email(self):
        serializer = CustomUserSerializer(data={'email': 'not-an-email', 'password': 'pass'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_create_with_duplicate_email(self):
        CustomUser.objects.create_user(email='dup@example.com', password='pass')
        serializer = CustomUserSerializer(data={'email': 'dup@example.com', 'password': 'pass2'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_password_min_length(self):
        serializer = CustomUserSerializer(data={'email': 'short@example.com', 'password': '1'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_to_representation_hides_fields_for_other_users(self):
        user1 = CustomUser.objects.create_user(email='u1@example.com', password='pass')
        user2 = CustomUser.objects.create_user(email='u2@example.com', password='pass')

        # Имитируем request с текущим пользователем user1
        class FakeRequest:
            user = user1

        serializer = CustomUserSerializer(user2, context={'request': FakeRequest()})
        data = serializer.data
        self.assertNotIn('password', data)
        self.assertEqual(set(data.keys()), {'id', 'email', 'phone_number', 'city'})


class TestUserAPI(APITestCase):
    """Интеграционные тесты API пользователей."""

    def setUp(self):
        # self.client уже создан автоматически как APIClient
        self.register_url = reverse('users:register')
        self.login_url = reverse('users:login')

    def test_register_user(self):
        data = {'email': 'reg@example.com', 'password': 'pass1234'}
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CustomUser.objects.filter(email='reg@example.com').exists())

    def test_login_returns_jwt(self):
        CustomUser.objects.create_user(email='login@example.com', password='pass1234')
        response = self.client.post(
            self.login_url,
            {'email': 'login@example.com', 'password': 'pass1234'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_get_user_profile_requires_auth(self):
        url = reverse('users:users-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_can_update_own_profile(self):
        user = CustomUser.objects.create_user(email='owner@example.com', password='pass')
        self.client.force_authenticate(user=user)
        url = reverse('users:users-detail', args=[user.id])
        response = self.client.patch(url, {'city': 'Казань'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.city, 'Казань')

    def test_user_cannot_update_other_profile(self):
        user1 = CustomUser.objects.create_user(email='a@example.com', password='pass')
        user2 = CustomUser.objects.create_user(email='b@example.com', password='pass')
        self.client.force_authenticate(user=user1)
        url = reverse('users:users-detail', args=[user2.id])
        response = self.client.patch(url, {'city': 'Сочи'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
