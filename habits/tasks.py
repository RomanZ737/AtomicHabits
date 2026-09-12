import telebot
from dotenv import load_dotenv
import os
import logging
from celery import shared_task
from django.utils import timezone
from .models import Habit

load_dotenv()

logger = logging.getLogger(__name__)


@shared_task
def send_telegram_message(chat_id, message):
    """Отправка сообщения в Телеграм"""
    try:
        crewbot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        bot = telebot.TeleBot(crewbot_token, parse_mode="html")
        bot.send_message(chat_id=chat_id, text=message)
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения пользователю {chat_id}: {e}")


@shared_task
def habit_reminder():
    """Проверяет привычки и отправляет напоминания."""
    now = timezone.localtime(timezone.now())
    # current_time = now.strftime("%H:%M")

    habits = Habit.objects.filter(
        is_pleasant_habit=False,
        action_time__hour=now.hour,
        action_time__minute=now.minute,
    ).select_related("owner", "connected_habit")

    for habit in habits:
        user = habit.owner
        if not user.telegram_chat_id:
            continue  # нет chat_id, пропускаем

        if habit.period > 1:
            last_reminder = habit.last_reminder_date
            if last_reminder:
                days_since = (now.date() - last_reminder).days
                if days_since < habit.period:
                    continue  # ещё рано напоминать

        # Формируем текст сообщения
        message = f"Напоминание о привычке: {habit.name}\n"
        message += f"Действие: {habit.action}\n"
        message += f"Место: {habit.habit_location}\n"
        message += f"Время: {habit.action_time}\n"

        if habit.connected_habit:
            message += f"Связанная приятная привычка: {habit.connected_habit.name}\n"
            message += f"Действие приятной привычки: {habit.connected_habit.action}\n"
        elif habit.bonus:
            message += f"Вознаграждение: {habit.bonus}\n"

        # Отправляем асинхронно

        send_telegram_message.delay(user.telegram_chat_id, message)

        # Обновляем дату последнего напоминания
        habit.last_reminder_date = now.date()
        habit.save(update_fields=["last_reminder_date"])
