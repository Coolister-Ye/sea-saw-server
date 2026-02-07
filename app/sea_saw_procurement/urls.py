from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NestedPurchaseOrderViewSet

router = DefaultRouter()
router.register(
    r"nested-purchase-orders",
    NestedPurchaseOrderViewSet,
    basename="nested-purchase-order",
)

app_name = "sea_saw_procurement"
urlpatterns = [
    path("", include(router.urls)),
]
