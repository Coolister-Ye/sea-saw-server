from django.urls import path

from sea_saw_auth.views import UserDetailView

app_name = "sea_saw_auth"

urlpatterns = [
    path('user-detail/', UserDetailView.as_view(), name='user-detail'),
]