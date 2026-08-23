from rest_framework import serializers
from habits.models import Habit
from .validators import validate_period, validate_time_for_action

class HabitSerializer(serializers.ModelSerializer):
    time_for_action = serializers.IntegerField(validators=[validate_time_for_action])
    period = serializers.IntegerField(required=False, default=1, validators=[validate_period])

    class Meta:
        model = Habit
        fields = '__all__'

    def validate(self, attrs):
        if attrs.get('connected_habit') and attrs.get('bonus'):
            raise serializers.ValidationError(
                "Нельзя указывать одновременно связанную привычку и вознаграждение.")
        if attrs.get('is_pleasant_habit'):
            if attrs.get('bonus') or attrs.get('connected_habit'):
                raise serializers.ValidationError(
                    "У приятной привычки не может быть вознаграждения или связанной привычки.")
        else:
            connected_habit = attrs.get('connected_habit')
            if connected_habit and not connected_habit.is_pleasant_habit:
                raise serializers.ValidationError("Связанная привычка должна быть приятной.")