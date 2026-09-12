from rest_framework import serializers


def validate_time_for_action(value: int):
    """Валидатор максимального и минимального времени выполнения привычки"""
    if value <= 0:
        raise serializers.ValidationError(
            "Время выполнения привычке не может быть меньше одной секунды"
        )
    elif value > 120:
        raise serializers.ValidationError(
            "Время выполнения привычке не может быть больше 120 секунд"
        )


def validate_period(value: int):
    """Валидатор минимальной и максимальной периодичности выполнения привычки"""
    if value < 1:
        raise serializers.ValidationError(
            "Периодичность выполнения привычки не может меньше одного дня"
        )
    elif value > 7:
        raise serializers.ValidationError(
            "Периодичность выполнения привычки не может быть больше 7 дней"
        )
