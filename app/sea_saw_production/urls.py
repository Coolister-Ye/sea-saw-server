from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductionOrderViewSet, NestedProductionOrderViewSet

router = DefaultRouter()
router.register(r"production-orders", ProductionOrderViewSet, basename="production-order")
router.register(
    r"nested-production-orders",
    NestedProductionOrderViewSet,
    basename="nested-production-order",
)

app_name = "sea_saw_production"
urlpatterns = [
    path("", include(router.urls)),
]
