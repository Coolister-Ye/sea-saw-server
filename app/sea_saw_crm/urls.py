from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AccountViewSet, ContactViewSet

router = DefaultRouter()
router.register(r"accounts", AccountViewSet)
router.register(r"contacts", ContactViewSet)

app_name = "sea-saw-crm"
urlpatterns = [
    path("", include(router.urls)),
]
