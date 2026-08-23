from django.db import models
from django.db.models import PROTECT


class Habit(models.Model):

    name = models.CharField(max_length=100, verbose_name='Habit name', help_text='Название привычки')
    habit_location = models.CharField(max_length=100, verbose_name='Habit Place',
                                      help_text='место, в котором необходимо выполнять привычку')
    owner = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, verbose_name='Habit Owner',
                              help_text='Создатель привычки', null=True, blank=True)
    action_time = models.TimeField(verbose_name='Habit Action Time',
                                       help_text='Время, когда необходимо выполнить привычку')
    action = models.TextField(verbose_name='Habit Action', help_text=' действие, которое представляет собой привычка')
    is_pleasant_habit = models.BooleanField(default=False, verbose_name='Is Habit Pleasant',
                                            help_text='Признак приятной привычки')
    connected_habit = models.ForeignKey('habits.Habit', on_delete=models.PROTECT, blank=True, null=True,
                                        verbose_name='Habit Connected', related_name='related_habit',
                                        help_text='Привычка, которую можно привязать к выполнению полезной привычки')
    period = models.IntegerField(verbose_name='Habit Period', default=1,
                              help_text='Периодичность выполнения привычки для напоминания в днях.')
    bonus = models.CharField(max_length=200, blank=True, null=True,
                             verbose_name='Habit Bonus',
                             help_text='Вознаграждение за выполнение привычки')
    time_for_action = models.IntegerField(verbose_name='Habit Time For Action', help_text='Время на выполнение привычки')
    is_public = models.BooleanField(default=False, verbose_name='Habit Public Habit',
                                    help_text='Признак публичности привычки')

    last_reminder_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'Привычка'
        verbose_name_plural = 'Привычки'

    def __str__(self):
        return self.name



