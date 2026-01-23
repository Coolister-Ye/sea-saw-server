"""
Payment-related mixins for views

Updated to support the new Payment model with Pipeline integration
and all payment types (Order, PurchaseOrder, ProductionOrder, OutboundOrder).
"""
from django.contrib.contenttypes.models import ContentType
from django.db import models
from rest_framework.exceptions import PermissionDenied, ValidationError


class PaymentRoleSerializerMixin:
    """
    Mixin for handling role-based serializer selection for payments.
    Reduces code duplication in payment viewsets.
    """

    # Subclasses should define these mappings
    role_serializer_map = {}

    def get_serializer_class(self):
        """Return role-based serializer based on user role."""
        user = self.request.user
        role = getattr(user.role, "role_type", None)
        return self.role_serializer_map.get(role, self.serializer_class)

    def get_user_role(self):
        """Get the current user's role type."""
        return getattr(self.request.user.role, "role_type", None)


class PaymentQuerysetFilterMixin:
    """
    Mixin for filtering payment querysets based on user permissions.

    Supports all payment-related entities:
    - Order (OrderPayment)
    - PurchaseOrder (PurchasePayment)
    - ProductionOrder (ProductionPayment)
    - OutboundOrder (OutboundPayment)
    """

    def get_payment_related_content_types(self):
        """
        Get ContentType objects for all payment-related models.
        Returns a dict mapping model names to ContentType objects.
        """
        from ..models import Order, PurchaseOrder, ProductionOrder, OutboundOrder

        return {
            "order": ContentType.objects.get_for_model(Order),
            "purchase_order": ContentType.objects.get_for_model(PurchaseOrder),
            "production_order": ContentType.objects.get_for_model(ProductionOrder),
            "outbound_order": ContentType.objects.get_for_model(OutboundOrder),
        }

    def filter_queryset_by_ownership(self, queryset, user):
        """
        Filter payments to only show those related to objects owned by the user.
        Used for SALE role users.

        Args:
            queryset: Payment queryset to filter
            user: User to filter by ownership

        Returns:
            Filtered queryset showing only payments for user-owned entities
        """
        from ..models import Order, PurchaseOrder, ProductionOrder, OutboundOrder

        content_types = self.get_payment_related_content_types()

        # Get IDs of entities owned by user
        owned_order_ids = Order.objects.filter(owner=user).values_list("id", flat=True)
        owned_purchase_order_ids = PurchaseOrder.objects.filter(owner=user).values_list(
            "id", flat=True
        )
        owned_production_order_ids = ProductionOrder.objects.filter(
            owner=user
        ).values_list("id", flat=True)
        owned_outbound_order_ids = OutboundOrder.objects.filter(owner=user).values_list(
            "id", flat=True
        )

        # Build Q objects for each entity type
        q_filters = (
            models.Q(
                content_type=content_types["order"], object_id__in=owned_order_ids
            )
            | models.Q(
                content_type=content_types["purchase_order"],
                object_id__in=owned_purchase_order_ids,
            )
            | models.Q(
                content_type=content_types["production_order"],
                object_id__in=owned_production_order_ids,
            )
            | models.Q(
                content_type=content_types["outbound_order"],
                object_id__in=owned_outbound_order_ids,
            )
        )

        return queryset.filter(q_filters)


class PaymentContentTypeHelperMixin:
    """
    Mixin providing helper methods for working with ContentType in payment context.

    Supports all payment entity types: Order, PurchaseOrder, ProductionOrder, OutboundOrder.
    """

    # Mapping of query parameter names to model classes
    PAYMENT_ENTITY_PARAMS = {
        "order": "Order",
        "purchase_order": "PurchaseOrder",
        "production_order": "ProductionOrder",
        "outbound_order": "OutboundOrder",
    }

    def get_content_type_for_model(self, model_name):
        """
        Get ContentType for a payment-related model.

        Args:
            model_name: One of 'order', 'purchase_order', 'production_order', 'outbound_order'

        Returns:
            ContentType object or None if invalid model_name
        """
        from ..models import Order, PurchaseOrder, ProductionOrder, OutboundOrder

        model_map = {
            "order": Order,
            "purchase_order": PurchaseOrder,
            "production_order": ProductionOrder,
            "outbound_order": OutboundOrder,
        }

        model_class = model_map.get(model_name)
        if model_class:
            return ContentType.objects.get_for_model(model_class)
        return None

    def get_content_type_from_params(self):
        """
        Extract content_type and object_id from query parameters.

        Checks for: order, purchase_order, production_order, outbound_order

        Returns:
            Tuple of (content_type, object_id, param_type) where:
            - content_type: ContentType object
            - object_id: ID of the related entity
            - param_type: One of 'order', 'purchase_order', 'production_order', 'outbound_order', or None
        """
        for param_name in self.PAYMENT_ENTITY_PARAMS.keys():
            entity_id = self.request.query_params.get(param_name)
            if entity_id:
                content_type = self.get_content_type_for_model(param_name)
                return content_type, entity_id, param_name

        return None, None, None

    def validate_related_object_exists_and_owned(
        self, param_type, object_id, user, role
    ):
        """
        Validate that the related object exists and is owned by the user (for SALE role).

        Args:
            param_type: One of 'order', 'purchase_order', 'production_order', 'outbound_order'
            object_id: ID of the related object
            user: User making the request
            role: User's role type

        Raises:
            ValidationError: If object doesn't exist
            PermissionDenied: If user doesn't have permission (SALE role only)

        Returns:
            The related object if validation passes
        """
        from ..models import Order, PurchaseOrder, ProductionOrder, OutboundOrder

        model_map = {
            "order": Order,
            "purchase_order": PurchaseOrder,
            "production_order": ProductionOrder,
            "outbound_order": OutboundOrder,
        }

        model_class = model_map.get(param_type)
        if not model_class:
            raise ValidationError(
                {param_type: f"Invalid entity type: {param_type}"}
            )

        # Try to get the object
        try:
            obj = model_class.objects.get(pk=object_id)
        except model_class.DoesNotExist:
            raise ValidationError(
                {param_type: f"{model_class.__name__} with id {object_id} does not exist"}
            )

        # Check ownership for SALE role
        if role == "SALE" and obj.owner != user:
            raise PermissionDenied(
                f"You can only create payments for your own {model_class.__name__.lower()}s"
            )

        return obj

    def get_pipeline_from_related_object(self, param_type, object_id):
        """
        Get the Pipeline associated with a related object.

        Args:
            param_type: One of 'order', 'purchase_order', 'production_order', 'outbound_order'
            object_id: ID of the related object

        Returns:
            Pipeline object or None
        """
        from ..models import Order, PurchaseOrder, ProductionOrder, OutboundOrder

        model_map = {
            "order": Order,
            "purchase_order": PurchaseOrder,
            "production_order": ProductionOrder,
            "outbound_order": OutboundOrder,
        }

        model_class = model_map.get(param_type)
        if not model_class:
            return None

        try:
            obj = model_class.objects.get(pk=object_id)
            return getattr(obj, "pipeline", None)
        except model_class.DoesNotExist:
            return None
