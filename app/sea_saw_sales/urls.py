"""
URL Configuration for sea_saw_sales app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import OrderViewSet, NestedOrderViewSet, OrderIntegrationViewSet

router = DefaultRouter()
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"nested-orders", NestedOrderViewSet, basename="nested-order")
router.register(r"orders-integration", OrderIntegrationViewSet, basename="order-integration")

app_name = "sea_saw_sales"
urlpatterns = [
    path("", include(router.urls)),
]
