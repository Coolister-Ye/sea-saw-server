"""
Sea-Saw Warehouse URLs
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import NestedOutboundOrderViewSet

app_name = "sea_saw_warehouse"

router = DefaultRouter()
router.register(
    r"nested-outbound-orders",
    NestedOutboundOrderViewSet,
    basename="nested-outbound-order",
)

urlpatterns = router.urls
