from django.urls import path

from sea_saw_auth.views import (
    UserDetailView,
    UserRegisterView,
    UserProfileUpdateView,
)

app_name = "sea_saw_auth"

urlpatterns = [
    path("user-detail/", UserDetailView.as_view(), name="user-detail"),
    path("register/", UserRegisterView.as_view(), name="register"),
    path("profile/update/", UserProfileUpdateView.as_view(), name="profile-update"),
]
