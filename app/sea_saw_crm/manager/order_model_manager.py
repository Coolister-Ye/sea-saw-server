"""
Order Model Manager - Handles Order operations with Pipeline synchronization

负责:
- Order数据更新时自动同步Pipeline字段
- 支持批量更新和单个实例更新
- 维护Order和Pipeline之间的数据一致性
"""

from .base_model_manager import BaseModelManager
from django.db import transaction


class OrderModelManager(BaseModelManager):
    """
    Order Manager - Manages Order operations with Pipeline synchronization

    Features:
    - Auto-sync pipeline fields when order data changes
    - Batch update support with pipeline sync
    - Maintains data consistency between Order and Pipeline
    """

    @transaction.atomic
    def update_with_pipeline(self, order_id=None, instance=None, user=None, **update_fields):
        """
        Update Order and automatically sync related Pipeline fields

        This method updates the order and propagates relevant changes to its pipeline:
        - contact: Syncs to pipeline.contact
        - order_date: Syncs to pipeline.order_date
        - total_amount: Syncs to pipeline.total_amount

        Args:
            order_id: Order ID to update (if not providing instance)
            instance: Order instance to update (if not providing order_id)
            user: User performing the update
            **update_fields: Fields to update on the order

        Returns:
            Updated Order instance

        Raises:
            ValueError: If neither order_id nor instance is provided

        Example:
            # Update by ID
            order = Order.objects.update_with_pipeline(
                order_id=5,
                user=request.user,
                contact=new_contact,
                order_date=new_date
            )

            # Update by instance
            order = Order.objects.update_with_pipeline(
                instance=my_order,
                user=request.user,
                status='confirmed'
            )
        """
        # Get the order instance
        if instance is None and order_id is None:
            raise ValueError("Either order_id or instance must be provided")

        if instance is None:
            instance = self.get(pk=order_id)

        # Prepare update fields with user tracking
        if user:
            update_fields["updated_by"] = user

        # Filter out reverse relation fields that cannot be directly assigned
        # These should be handled by serializers, not by the manager
        filtered_fields = {}
        for field_name, value in update_fields.items():
            try:
                field = instance._meta.get_field(field_name)
                # Skip reverse relations (one_to_many or auto-created many_to_many)
                if field.one_to_many or (field.many_to_many and field.auto_created):
                    continue
                filtered_fields[field_name] = value
            except Exception:
                # If field doesn't exist in model metadata, skip it
                continue

        # Update the order with filtered fields
        for field, value in filtered_fields.items():
            setattr(instance, field, value)
        instance.save()

        # Sync to pipeline if it exists
        if hasattr(instance, 'pipeline') and instance.pipeline:
            self._sync_to_pipeline(instance, user)

        return instance

    @transaction.atomic
    def bulk_update_with_pipeline(self, queryset, user=None, **update_fields):
        """
        Bulk update orders and sync their pipelines

        Args:
            queryset: QuerySet of orders to update
            user: User performing the update
            **update_fields: Fields to update on all orders

        Returns:
            Number of orders updated

        Example:
            Order.objects.bulk_update_with_pipeline(
                queryset=Order.objects.filter(status='draft'),
                user=request.user,
                status='pending'
            )
        """
        # Prepare update fields with user tracking
        if user:
            update_fields["updated_by"] = user

        # Update all orders
        count = queryset.update(**update_fields)

        # Sync each order's pipeline
        for order in queryset.select_related('pipeline'):
            if hasattr(order, 'pipeline') and order.pipeline:
                self._sync_to_pipeline(order, user)

        return count

    def _sync_to_pipeline(self, order, user=None):
        """
        Synchronize order data to its related pipeline

        This internal method updates pipeline fields that should mirror order data:
        - contact: Customer contact
        - order_date: Order date
        - total_amount: Total amount

        Args:
            order: Order instance to sync from
            user: User performing the sync (for audit tracking)
        """
        from ..models.pipeline import Pipeline

        pipeline = order.pipeline
        update_fields = []

        # Sync contact if changed
        if pipeline.contact != order.contact:
            pipeline.contact = order.contact
            update_fields.append('contact')

        # Sync order_date if changed
        if pipeline.order_date != order.order_date:
            pipeline.order_date = order.order_date
            update_fields.append('order_date')

        # Save if there are changes
        if update_fields:
            if user:
                pipeline.updated_by = user
                update_fields.append('updated_by')

            # Always include updated_at
            update_fields.append('updated_at')
            pipeline.save(update_fields=update_fields)
