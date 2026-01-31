from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ContactViewSet,
    CompanyViewSet,
    OrderViewSet,
    NestedOrderViewSet,
    PipelineViewSet,
    FieldListView,
    PaymentViewSet,
    NestedPaymentViewSet,
    PaymentRecordViewSet,  # Legacy alias
    NestedPaymentRecordViewSet,  # Legacy alias
    ProductionOrderViewSet,
    NestedProductionOrderViewSet,
    NestedPurchaseOrderViewSet,
    NestedOutboundOrderViewSet,
    ContentTypeView,
    SecureAttachmentDownloadView,
)

router = DefaultRouter()
router.register(r"contacts", ContactViewSet)
router.register(r"companies", CompanyViewSet)
router.register(r"orders", OrderViewSet)
router.register(r"nested-orders", NestedOrderViewSet, basename="nested-order")
router.register(r"pipelines", PipelineViewSet)
router.register(r"payments", PaymentViewSet)
router.register(r"nested-payments", NestedPaymentViewSet, basename="nested-payment")
# Legacy endpoints for backward compatibility
router.register(r"payment-records", PaymentRecordViewSet, basename="payment-record")
router.register(
    r"nested-payment-records",
    NestedPaymentRecordViewSet,
    basename="nested-payment-record",
)
router.register(r"production-orders", ProductionOrderViewSet)
router.register(
    r"nested-production-orders",
    NestedProductionOrderViewSet,
    basename="nested-production-order",
)
router.register(
    r"nested-purchase-orders",
    NestedPurchaseOrderViewSet,
    basename="nested-purchase-order",
)
router.register(
    r"nested-outbound-orders",
    NestedOutboundOrderViewSet,
    basename="nested-outbound-order",
)
router.register(r"fields", FieldListView)

app_name = "sea-saw-crm"
urlpatterns = [
    path("", include(router.urls)),
    path("content-types/", ContentTypeView.as_view(), name="content-types"),
    path(
        "attachments/<int:attachment_id>/download/",
        SecureAttachmentDownloadView.as_view(),
        name="attachment-download",
    ),
]
