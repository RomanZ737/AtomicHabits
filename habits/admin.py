from django.contrib import admin
from .models import Habit

@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ('owner', 'action_time', 'action', 'is_pleasant_habit', 'is_public')
    list_filter = ('owner', 'action_time')

    class Meta:
        model = Habit
