from django.urls import path, include
from rest_framework.routers import DefaultRouter

from sea_saw_preference import views

router = DefaultRouter()
router.register("custom-views", views.CustomViewViewSet, basename="custom-view")

app_name = "sea_saw_preference"
urlpatterns = [
    path("", include(router.urls)),
]
