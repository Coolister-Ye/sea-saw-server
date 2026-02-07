"""
URL Configuration for sea_saw_finance app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    PaymentViewSet,
    NestedPaymentViewSet,
    # Legacy aliases
    PaymentRecordViewSet,
    NestedPaymentRecordViewSet,
)

router = DefaultRouter()
router.register(r"payments", PaymentViewSet, basename="payment")
router.register(r"nested-payments", NestedPaymentViewSet, basename="nested-payment")

# Legacy aliases for backward compatibility
router.register(r"payment-records", PaymentRecordViewSet, basename="payment-record")
router.register(r"nested-payment-records", NestedPaymentRecordViewSet, basename="nested-payment-record")

app_name = "sea_saw_finance"
urlpatterns = [
    path("", include(router.urls)),
]
