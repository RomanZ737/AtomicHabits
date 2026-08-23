from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from habits.models import Habit
from rest_framework import serializers

from habits.paginators import HabitsPaginator
from habits.serializers import HabitSerializer
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from .permissions import IsOwner


class MyHabitViewSet(viewsets.ModelViewSet):
    serializer_class = HabitSerializer
    pagination_class = HabitsPaginator
    permission_classes = [IsAuthenticated, IsOwner]  # для update/destroy

    def get_queryset(self):
        return Habit.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PublicHabitViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = HabitSerializer
    pagination_class = HabitsPaginator
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Habit.objects.filter(is_public=True)