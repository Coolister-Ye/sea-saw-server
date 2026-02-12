"""
Django Signals for Bidirectional Status Synchronization

Implements reverse sync: When sub-entity status changes, potentially update Pipeline.

Signal Flow:
1. pre_save captures old status before save
2. post_save triggers reverse sync if status changed
3. StatusSyncService handles the actual sync logic

Loop Prevention:
- Forward sync uses bulk .update() which bypasses signals
- _skip_status_sync flag can be set to skip reverse sync when needed
"""

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from sea_saw_production.models import ProductionOrder
from sea_saw_procurement.models import PurchaseOrder
from sea_saw_warehouse.models import OutboundOrder


# ============================================================================
# ProductionOrder Signals
# ============================================================================


@receiver(pre_save, sender=ProductionOrder)
def capture_production_old_status(sender, instance, **kwargs):
    """
    Capture old status before save for comparison in post_save.
    Only captures for existing instances (has pk).
    """
    if instance.pk:
        try:
            old_instance = ProductionOrder.all_objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except ProductionOrder.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=ProductionOrder)
def sync_production_status_change(sender, instance, created, **kwargs):
    """
    Trigger reverse sync when ProductionOrder status changes.

    Skips if:
    - Newly created (no previous status to compare)
    - Status unchanged
    - _skip_status_sync flag is set (prevents loops)
    - No pipeline associated
    """
    if created:
        return

    old_status = getattr(instance, "_old_status", None)
    new_status = instance.status

    if old_status and old_status != new_status:
        # Check if sync should be skipped (loop prevention)
        if getattr(instance, "_skip_status_sync", False):
            return

        # Ensure instance has a pipeline
        if not instance.pipeline_id:
            return

        from sea_saw_pipeline.services.status_sync_service import StatusSyncService

        StatusSyncService.sync_subentity_to_pipeline(
            subentity=instance,
            entity_type="production",
            old_status=old_status,
            new_status=new_status,
            user=getattr(instance, "updated_by", None),
        )


# ============================================================================
# PurchaseOrder Signals
# ============================================================================


@receiver(pre_save, sender=PurchaseOrder)
def capture_purchase_old_status(sender, instance, **kwargs):
    """
    Capture old status before save for comparison in post_save.
    """
    if instance.pk:
        try:
            old_instance = PurchaseOrder.all_objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except PurchaseOrder.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=PurchaseOrder)
def sync_purchase_status_change(sender, instance, created, **kwargs):
    """
    Trigger reverse sync when PurchaseOrder status changes.
    """
    if created:
        return

    old_status = getattr(instance, "_old_status", None)
    new_status = instance.status

    if old_status and old_status != new_status:
        if getattr(instance, "_skip_status_sync", False):
            return

        if not instance.pipeline_id:
            return

        from sea_saw_pipeline.services.status_sync_service import StatusSyncService

        StatusSyncService.sync_subentity_to_pipeline(
            subentity=instance,
            entity_type="purchase",
            old_status=old_status,
            new_status=new_status,
            user=getattr(instance, "updated_by", None),
        )


# ============================================================================
# OutboundOrder Signals
# ============================================================================


@receiver(pre_save, sender=OutboundOrder)
def capture_outbound_old_status(sender, instance, **kwargs):
    """
    Capture old status before save for comparison in post_save.
    """
    if instance.pk:
        try:
            old_instance = OutboundOrder.all_objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except OutboundOrder.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=OutboundOrder)
def sync_outbound_status_change(sender, instance, created, **kwargs):
    """
    Trigger reverse sync when OutboundOrder status changes.
    """
    if created:
        return

    old_status = getattr(instance, "_old_status", None)
    new_status = instance.status

    if old_status and old_status != new_status:
        if getattr(instance, "_skip_status_sync", False):
            return

        if not instance.pipeline_id:
            return

        from sea_saw_pipeline.services.status_sync_service import StatusSyncService

        StatusSyncService.sync_subentity_to_pipeline(
            subentity=instance,
            entity_type="outbound",
            old_status=old_status,
            new_status=new_status,
            user=getattr(instance, "updated_by", None),
        )
