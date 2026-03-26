from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PurchaseOrderViewSet, NestedPurchaseOrderViewSet

router = DefaultRouter()
router.register(
    r"purchase-orders",
    PurchaseOrderViewSet,
    basename="purchase-order",
)
router.register(
    r"nested-purchase-orders",
    NestedPurchaseOrderViewSet,
    basename="nested-purchase-order",
)

app_name = "sea_saw_procurement"
urlpatterns = [
    path("", include(router.urls)),
]
