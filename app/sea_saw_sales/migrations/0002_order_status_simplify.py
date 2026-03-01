"""
Migration: Simplify Order.status from 5-state to 3-state.

Design change: Order.status is now an independent sales document lifecycle
(draft / confirmed / cancelled), decoupled from Pipeline status.
Fulfillment tracking is done via order.pipeline.status.

Data mapping:
  active         → confirmed
  completed      → confirmed
  issue_reported → confirmed
  draft          → draft (unchanged)
  cancelled      → cancelled (unchanged)
"""

from django.db import migrations, models


def migrate_order_status_forward(apps, schema_editor):
    Order = apps.get_model("sea_saw_sales", "Order")
    Order.objects.filter(
        status__in=["active", "completed", "issue_reported"]
    ).update(status="confirmed")


def migrate_order_status_backward(apps, schema_editor):
    # Cannot perfectly reverse — map all confirmed → active (best approximation)
    Order = apps.get_model("sea_saw_sales", "Order")
    Order.objects.filter(status="confirmed").update(status="active")


class Migration(migrations.Migration):

    dependencies = [
        ("sea_saw_sales", "0001_initial"),
    ]

    operations = [
        # Step 1: Data migration — remap old statuses to 'confirmed'
        migrations.RunPython(
            migrate_order_status_forward,
            reverse_code=migrate_order_status_backward,
        ),
        # Step 2: Update field choices to new 3-state definition
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Draft"),
                    ("confirmed", "Confirmed"),
                    ("cancelled", "Cancelled"),
                ],
                default="draft",
                max_length=50,
                verbose_name="Status",
            ),
        ),
    ]
