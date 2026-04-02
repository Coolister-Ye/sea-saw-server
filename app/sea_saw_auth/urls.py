from django.urls import path, include
from rest_framework.routers import DefaultRouter

from sea_saw_auth.views import (
    UserDetailView,
    UserRegisterView,
    UserProfileUpdateView,
    AdminUserViewSet,
    RoleViewSet,
)

router = DefaultRouter()
router.register(r"admin/users", AdminUserViewSet, basename="admin-user")
router.register(r"admin/roles", RoleViewSet, basename="admin-role")

app_name = "sea_saw_auth"

urlpatterns = [
    path("user-detail/", UserDetailView.as_view(), name="user-detail"),
    path("register/", UserRegisterView.as_view(), name="register"),
    path("profile/update/", UserProfileUpdateView.as_view(), name="profile-update"),
    path("", include(router.urls)),
]
