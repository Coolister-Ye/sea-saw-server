from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AccountViewSet, ContactViewSet, BankAccountViewSet

router = DefaultRouter()
router.register(r"accounts", AccountViewSet)
router.register(r"contacts", ContactViewSet)
router.register(r"bank-accounts", BankAccountViewSet)

app_name = "sea-saw-crm"
urlpatterns = [
    path("", include(router.urls)),
]
