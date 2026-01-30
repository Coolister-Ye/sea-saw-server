"""
Serializer Mixins for common functionality
"""


class PipelineSyncMixin:
    """
    Mixin to automatically sync Order data to related Pipeline.

    When an Order is updated, certain fields should be synced to its Pipeline:
    - contact → pipeline.contact
    - order_date → pipeline.order_date

    Usage:
        class MyOrderSerializer(PipelineSyncMixin, BaseSerializer):
            def update(self, instance, validated_data):
                instance = super().update(instance, validated_data)
                self.sync_to_pipeline(instance)
                return instance
    """

    def sync_to_pipeline(self, order):
        """
        Synchronize order data to its related pipeline

        Args:
            order: Order instance to sync from
        """
        if not hasattr(order, "pipeline") or not order.pipeline:
            return

        pipeline = order.pipeline
        update_fields = []

        # Sync company if changed
        if pipeline.company != order.company:
            pipeline.company = order.company
            update_fields.append("company")

        # Sync contact if changed
        if pipeline.contact != order.contact:
            pipeline.contact = order.contact
            update_fields.append("contact")

        # Sync order_date if changed
        if pipeline.order_date != order.order_date:
            pipeline.order_date = order.order_date
            update_fields.append("order_date")

        # Save if there are changes
        if update_fields:
            # Get user from context for audit tracking
            request = self.context.get("request")
            if request and hasattr(request, "user"):
                pipeline.updated_by = request.user
                update_fields.append("updated_by")

            # Always include updated_at
            update_fields.append("updated_at")
            pipeline.save(update_fields=update_fields)
