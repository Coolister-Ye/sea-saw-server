from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ContactViewSet,
    CompanyViewSet,
    ProxyOrderViewSet,
    FieldListView,
    PaymentRecordViewSet,
)

router = DefaultRouter()
router.register(r"contacts", ContactViewSet)
router.register(r"companies", CompanyViewSet)
router.register(r"orders", ProxyOrderViewSet)
router.register(r"payments", PaymentRecordViewSet)
router.register(r"fields", FieldListView)

app_name = "sea-saw-crm"
urlpatterns = [
    path("", include(router.urls)),
]
