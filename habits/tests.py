# habits/tests.py
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from habits.models import Habit
from habits.serializers import HabitSerializer
from habits.validators import validate_time_for_action, validate_period
from users.models import CustomUser


class TestValidators(TestCase):
    """Тесты валидаторов habits."""

    def test_valid_time_for_action(self):
        for value in (1, 60, 120):
            with self.subTest(value=value):
                self.assertIsNone(validate_time_for_action(value))

    def test_invalid_time_for_action(self):
        for value in (0, -1, 121, 200):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    validate_time_for_action(value)

    def test_valid_period(self):
        for value in (1, 4, 7):
            with self.subTest(value=value):
                self.assertIsNone(validate_period(value))

    def test_invalid_period(self):
        for value in (0, -1, 8, 30):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    validate_period(value)


class TestHabitSerializer(TestCase):
    """Тесты сериализатора привычек."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(email='h@example.com', password='pass')
        self.pleasant_habit = Habit.objects.create(
            name='Приятная',
            habit_location='Дом',
            action_time='08:00',
            action='Пить кофе',
            is_pleasant_habit=True,
            time_for_action=60,
            owner=self.user,
        )

    def test_valid_habit_creation(self):
        data = {
            'name': 'Зарядка',
            'habit_location': 'Спортзал',
            'action_time': '07:00',
            'action': 'Отжимания',
            'time_for_action': 60,
            'period': 1,
            'owner': self.user.id,
        }
        serializer = HabitSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_cannot_set_both_connected_habit_and_bonus(self):
        data = {
            'name': 'Полезная',
            'habit_location': 'Дом',
            'action_time': '09:00',
            'action': 'Чтение',
            'time_for_action': 60,
            'connected_habit': self.pleasant_habit.id,
            'bonus': 'Шоколадка',
            'owner': self.user.id,
        }
        serializer = HabitSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_pleasant_habit_cannot_have_bonus(self):
        data = {
            'name': 'Приятная с бонусом',
            'habit_location': 'Дом',
            'action_time': '10:00',
            'action': 'Смотреть кино',
            'time_for_action': 60,
            'is_pleasant_habit': True,
            'bonus': 'Попкорн',
            'owner': self.user.id,
        }
        serializer = HabitSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_connected_habit_must_be_pleasant(self):
        not_pleasant = Habit.objects.create(
            name='Неприятная',
            habit_location='Дом',
            action_time='06:00',
            action='Уборка',
            is_pleasant_habit=False,
            time_for_action=60,
            owner=self.user,
        )
        data = {
            'name': 'Полезная',
            'habit_location': 'Дом',
            'action_time': '11:00',
            'action': 'Учить Python',
            'time_for_action': 60,
            'connected_habit': not_pleasant.id,
            'owner': self.user.id,
        }
        serializer = HabitSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)


class TestMyHabitViewSet(APITestCase):
    """Тесты CRUD личных привычек."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(email='v@example.com', password='pass')
        self.other_user = CustomUser.objects.create_user(email='other@example.com', password='pass')
        self.habit = Habit.objects.create(
            name='Моя привычка',
            habit_location='Дом',
            action_time='08:00',
            action='Медитация',
            time_for_action=60,
            owner=self.user,
        )

    def test_list_requires_auth(self):
        url = reverse('habits:my-habits-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_sees_only_own_habits(self):
        Habit.objects.create(
            name='Чужая',
            habit_location='Офис',
            action_time='09:00',
            action='Работа',
            time_for_action=60,
            owner=self.other_user,
        )
        self.client.force_authenticate(user=self.user)
        url = reverse('habits:my-habits-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item['name'] for item in response.data['results']]
        self.assertIn('Моя привычка', names)
        self.assertNotIn('Чужая', names)

    def test_create_habit_sets_owner_automatically(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('habits:my-habits-list')
        data = {
            'name': 'Новая',
            'habit_location': 'Парк',
            'action_time': '10:00',
            'action': 'Бег',
            'time_for_action': 60,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        habit = Habit.objects.get(id=response.data['id'])
        self.assertEqual(habit.owner, self.user)

    def test_user_cannot_update_other_habit(self):
        self.client.force_authenticate(user=self.other_user)
        url = reverse('habits:my-habits-detail', args=[self.habit.id])
        response = self.client.patch(url, {'name': 'Взлом'})
        # queryset фильтруется по owner, поэтому 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_public_habits_only(self):
        Habit.objects.create(
            name='Публичная', habit_location='Дом', action_time='08:00',
            action='Публичная', time_for_action=60, is_public=True, owner=self.user,
        )
        Habit.objects.create(
            name='Приватная', habit_location='Дом', action_time='08:00',
            action='Приватная', time_for_action=60, is_public=False, owner=self.other_user,
        )
        self.client.force_authenticate(user=self.other_user)
        url = reverse('habits:public-habits-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item['name'] for item in response.data['results']]
        self.assertIn('Публичная', names)
        self.assertNotIn('Приватная', names)


class TestHabitReminderTask(TestCase):
    """Тесты Celery-задачи напоминаний."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='tg@example.com',
            password='pass',
            telegram_chat_id='123456789',
        )
        self.now = timezone.localtime(timezone.now())

    @patch('habits.tasks.send_telegram_message.delay')
    def test_sends_reminder_for_matching_habit(self, mock_send):
        habit = Habit.objects.create(
            name='Пить воду',
            habit_location='Кухня',
            action_time=self.now.time(),
            action='Выпить стакан воды',
            time_for_action=60,
            period=1,
            owner=self.user,
        )
        # импорт внутри метода, чтобы patch успел подмениться
        from habits.tasks import habit_reminder
        habit_reminder()

        mock_send.assert_called_once()
        args, kwargs = mock_send.call_args
        self.assertEqual(args[0], '123456789')
        self.assertIn('Пить воду', args[1])

        habit.refresh_from_db()
        self.assertEqual(habit.last_reminder_date, self.now.date())

    @patch('habits.tasks.send_telegram_message.delay')
    def test_does_not_send_if_no_telegram_id(self, mock_send):
        user = CustomUser.objects.create_user(email='no_tg@example.com', password='pass')
        Habit.objects.create(
            name='Без телеги', habit_location='Дом',
            action_time=self.now.time(), action='Тест',
            time_for_action=60, owner=user,
        )
        from habits.tasks import habit_reminder
        habit_reminder()
        mock_send.assert_not_called()

    @patch('habits.tasks.send_telegram_message.delay')
    def test_respects_period(self, mock_send):
        Habit.objects.create(
            name='Раз в 3 дня',
            habit_location='Дом',
            action_time=self.now.time(),
            action='Тест',
            time_for_action=60,
            period=3,
            last_reminder_date=self.now.date() - timedelta(days=1),
            owner=self.user,
        )
        from habits.tasks import habit_reminder
        habit_reminder()
        mock_send.assert_not_called()

    @patch('habits.tasks.send_telegram_message.delay')
    def test_skips_pleasant_habits(self, mock_send):
        Habit.objects.create(
            name='Приятная',
            habit_location='Дом',
            action_time=self.now.time(),
            action='Отдых',
            time_for_action=60,
            is_pleasant_habit=True,
            owner=self.user,
        )
        from habits.tasks import habit_reminder
        habit_reminder()
        mock_send.assert_not_called()
