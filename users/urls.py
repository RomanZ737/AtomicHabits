from .serializers import CustomUserSerializer
from .views import CustomUserViewSet, UserCreateAPIView
from rest_framework.routers import DefaultRouter
from .apps import UsersConfig
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from django.urls import path
from drf_yasg.utils import swagger_auto_schema
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)

app_name = UsersConfig.name

router = DefaultRouter()

router.register(r"", CustomUserViewSet, basename="users")

urlpatterns = [
    path(
        "register/",
        swagger_auto_schema(
            method="post",
            request_body=CustomUserSerializer,
            responses={201: CustomUserSerializer()},
        )(UserCreateAPIView.as_view()),
        name="register",
    ),
    path(
        "login/",
        swagger_auto_schema(
            method="post",
            request_body=TokenObtainPairSerializer,
            responses={200: TokenObtainPairSerializer()},
        )(TokenObtainPairView.as_view()),
        name="login",
    ),
    path(
        "token/refresh/",
        swagger_auto_schema(
            method="post",
            request_body=TokenRefreshSerializer,
            responses={200: TokenRefreshSerializer()},
        )(TokenRefreshView.as_view()),
        name="token_refresh",
    ),
] + router.urls
