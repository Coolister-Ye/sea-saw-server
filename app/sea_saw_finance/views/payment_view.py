# sea_saw_finance/views/payment_view.py
from django.db import models
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser, FormParser
from sea_saw_base.parsers import NestedMultiPartParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType

from ..models import Payment
from ..serializers import (
    PaymentStandaloneSerializerForAdmin,
    PaymentStandaloneSerializerForSales,
    PaymentNestedSerializerForAdmin,
    PaymentNestedSerializerForSales,
)
# Order serializers moved to sea_saw_sales app
from sea_saw_sales.serializers import (
    OrderSerializerForAdmin,
    OrderSerializerForSales,
)
from sea_saw_procurement.serializers import (
    PurchaseOrderSerializerForAdmin,
    PurchaseOrderSerializerForSales,
)
from sea_saw_pipeline.serializers.pipeline import (
    PipelineSerializerForAdmin,
    PipelineSerializerForSales,
    PipelineSerializerForProduction,
    PipelineSerializerForWarehouse,
)
from ..permissions import CanManagePayment
from sea_saw_base.metadata import BaseMetadata
from sea_saw_base.mixins import ReturnRelatedMixin
from ..mixins import (
    PaymentRoleSerializerMixin,
    PaymentQuerysetFilterMixin,
    PaymentContentTypeHelperMixin,
)


class PaymentViewSet(
    PaymentRoleSerializerMixin,
    PaymentQuerysetFilterMixin,
    ReturnRelatedMixin,
    ModelViewSet,
):
    """
    Standalone payment viewset for direct CRUD operations.
    Supports payments for Order, PurchaseOrder, ProductionOrder, and OutboundOrder via GenericForeignKey.
    """

    queryset = Payment.objects.select_related("content_type", "pipeline").prefetch_related(
        "attachments"
    )
    permission_classes = [IsAuthenticated, CanManagePayment]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    metadata_class = BaseMetadata
    parser_classes = (JSONParser, NestedMultiPartParser, FormParser)

    filterset_fields = ["content_type", "object_id", "currency", "payment_method", "payment_type", "pipeline"]
    ordering_fields = ["payment_date", "amount", "created_at"]
    ordering = ["-payment_date"]

    # ReturnRelatedMixin configuration (dynamic based on content_type)
    related_field_name = "related_object"

    # PaymentRoleSerializerMixin configuration
    role_serializer_map = {
        "SALE": PaymentStandaloneSerializerForSales,
        "ADMIN": PaymentStandaloneSerializerForAdmin,
    }
    serializer_class = PaymentStandaloneSerializerForAdmin  # Default

    def get_queryset(self):
        """Filter by user permissions.

        Only ADMIN and SALE roles can access (enforced by CanManagePayment).
        SALE users can only see their own orders/purchase orders/production orders/outbound orders.
        """
        base_queryset = super().get_queryset().filter(deleted__isnull=True)
        role = self.get_user_role()

        # SALE users: only see payments for their own entities
        if role == "SALE":
            base_queryset = self.filter_queryset_by_ownership(
                base_queryset, self.request.user
            )

        # ADMIN: see all payments (no filtering)
        return base_queryset

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            owner=self.request.user,
        )


class NestedPaymentViewSet(
    PaymentRoleSerializerMixin,
    PaymentQuerysetFilterMixin,
    PaymentContentTypeHelperMixin,
    ReturnRelatedMixin,
    ModelViewSet,
):
    """
    Nested payment viewset for creating/updating payments within entity context.

    Usage:
    - Create Order Payment: POST /api/finance/nested-payments/?order=123
    - Create Purchase Payment: POST /api/finance/nested-payments/?purchase_order=456
    - Create Production Payment: POST /api/finance/nested-payments/?production_order=789
    - Create Outbound Payment: POST /api/finance/nested-payments/?outbound_order=321
    - Update: PATCH /api/finance/nested-payments/999/?order=123

    Return Related Object:
    - ?return_related=true - Returns updated Pipeline data (default, recommended)
    - ?return_related=true&return_type=entity - Returns the specific entity (Order/PurchaseOrder/etc.)

    Features:
    - Auto-injects content_type and object_id from query parameter
    - Returns Pipeline or specific entity data when ?return_related=true
    - Supports file uploads (attachments)
    - Validates related object exists and prevents changes during update
    """

    queryset = Payment.objects.select_related("content_type", "pipeline").prefetch_related(
        "attachments"
    )
    permission_classes = [IsAuthenticated, CanManagePayment]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    metadata_class = BaseMetadata
    parser_classes = (JSONParser, NestedMultiPartParser, FormParser)

    filterset_fields = ["content_type", "object_id", "currency", "payment_method", "payment_type", "pipeline"]
    ordering_fields = ["payment_date", "amount", "created_at"]
    ordering = ["-payment_date"]

    # PaymentRoleSerializerMixin configuration
    role_serializer_map = {
        "SALE": PaymentNestedSerializerForSales,
        "ADMIN": PaymentNestedSerializerForAdmin,
    }
    serializer_class = PaymentNestedSerializerForAdmin  # Default

    # ReturnRelatedMixin configuration
    # Default to "pipeline" since it's the main entry point
    related_field_name = "pipeline"

    # Role-based Pipeline serializer map for ReturnRelatedMixin
    role_related_serializer_map = {
        "ADMIN": PipelineSerializerForAdmin,
        "SALE": PipelineSerializerForSales,
        "PRODUCTION": PipelineSerializerForProduction,
        "WAREHOUSE": PipelineSerializerForWarehouse,
    }

    def _get_related_object(self, instance):
        """
        Override to support dynamic related field based on return_type parameter.

        - return_type=pipeline (default): Returns Pipeline object
        - return_type=entity: Returns the specific entity (Order/PurchaseOrder/etc.)
        """
        return_type = self.request.query_params.get("return_type", "pipeline")

        if return_type == "entity":
            # Return the specific entity (Order, PurchaseOrder, etc.)
            return getattr(instance, "related_object", None)
        else:
            # Default: return Pipeline (main entry point)
            return getattr(instance, "pipeline", None)

    def get_related_serializer_class(self):
        """Return role-based serializer for related object.

        By default returns Pipeline serializer (main entry point).
        If ?return_type=entity is specified, returns the specific entity serializer.

        Only ADMIN and SALE roles can access payments (enforced by CanManagePayment).
        """
        role = self.get_user_role()
        return_type = self.request.query_params.get("return_type", "pipeline")

        # If explicitly requesting entity, return specific entity serializer
        if return_type == "entity":
            # Determine serializer based on query params and role
            if self.request.query_params.get("order"):
                return OrderSerializerForSales if role == "SALE" else OrderSerializerForAdmin

            if self.request.query_params.get("purchase_order"):
                return (
                    PurchaseOrderSerializerForSales
                    if role == "SALE"
                    else PurchaseOrderSerializerForAdmin
                )

            # TODO: Add serializers for ProductionOrder and OutboundOrder when needed
            # if self.request.query_params.get("production_order"):
            #     return ProductionOrderSerializerForSales if role == "SALE" else ProductionOrderSerializerForAdmin
            # if self.request.query_params.get("outbound_order"):
            #     return OutboundOrderSerializerForSales if role == "SALE" else OutboundOrderSerializerForAdmin

        # Default: return Pipeline serializer
        return self.role_related_serializer_map.get(
            role, PipelineSerializerForAdmin
        )

    def get_queryset(self):
        """Filter by related object query parameter and user permissions.

        Only ADMIN and SALE roles can access (enforced by CanManagePayment).
        SALE users can only see their own entities.
        """
        base_queryset = super().get_queryset().filter(deleted__isnull=True)
        role = self.get_user_role()

        # Filter by query parameter (order, purchase_order, production_order, outbound_order)
        content_type, object_id, param_type = self.get_content_type_from_params()

        if content_type and object_id:
            base_queryset = base_queryset.filter(
                content_type=content_type, object_id=object_id
            )

        # SALE users: only see payments for their own entities
        if role == "SALE":
            base_queryset = self.filter_queryset_by_ownership(
                base_queryset, self.request.user
            )

        # ADMIN: see all payments (no additional filtering)
        return base_queryset

    def get_serializer(self, *args, **kwargs):
        """Auto-inject content_type and object_id from query parameter into request data."""
        content_type, object_id, param_type = self.get_content_type_from_params()
        data = kwargs.get("data")

        if data and content_type and object_id:
            # Handle QueryDict (FormData)
            if hasattr(data, "_mutable"):
                data._mutable = True
                data["content_type"] = content_type.id
                data["object_id"] = object_id
                data._mutable = False
            # Handle dict (JSON)
            elif isinstance(data, dict):
                data["content_type"] = content_type.id
                data["object_id"] = object_id

            kwargs["data"] = data

        return super().get_serializer(*args, **kwargs)

    def perform_create(self, serializer):
        """Validate related object exists before creating payment."""
        content_type, object_id, param_type = self.get_content_type_from_params()
        user = self.request.user
        role = self.get_user_role()

        if not param_type:
            raise ValidationError(
                {
                    "related_object": (
                        "One of 'order', 'purchase_order', 'production_order', "
                        "or 'outbound_order' query parameter is required"
                    )
                }
            )

        # Validate related object exists and user has access
        related_obj = self.validate_related_object_exists_and_owned(
            param_type, object_id, user, role
        )

        # Auto-inject pipeline from related object if available
        pipeline = getattr(related_obj, "pipeline", None)
        extra_fields = {
            "created_by": user,
            "owner": user,
        }
        if pipeline:
            extra_fields["pipeline"] = pipeline

        serializer.save(**extra_fields)

    def perform_update(self, serializer):
        """Prevent changing related object during update."""
        content_type, object_id, param_type = self.get_content_type_from_params()
        instance = self.get_object()

        if param_type and content_type and object_id:
            # Validate related object hasn't changed
            if instance.content_type != content_type or str(
                instance.object_id
            ) != str(object_id):
                raise ValidationError(
                    {
                        param_type: f"Cannot change {param_type} association. Delete and recreate instead."
                    }
                )

        serializer.save()


# Legacy aliases for backward compatibility
PaymentRecordViewSet = PaymentViewSet
NestedPaymentRecordViewSet = NestedPaymentViewSet
