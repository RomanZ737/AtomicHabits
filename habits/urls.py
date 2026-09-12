from rest_framework.routers import DefaultRouter
from .views import MyHabitViewSet, PublicHabitViewSet
from .apps import HabitsConfig

app_name = HabitsConfig.name

router = DefaultRouter()
router.register(r"my-habits", MyHabitViewSet, basename="my-habits")
router.register(r"public-habits", PublicHabitViewSet, basename="public-habits")
urlpatterns = [] + router.urls
