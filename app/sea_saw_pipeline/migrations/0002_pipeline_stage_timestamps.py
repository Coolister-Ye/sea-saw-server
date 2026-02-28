
# Generated manually — adds per-stage timestamp fields to Pipeline

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sea_saw_pipeline", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="pipeline",
            name="in_purchase_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="In Purchase At",
                help_text="When purchase stage started",
            ),
        ),
        migrations.AddField(
            model_name="pipeline",
            name="purchase_completed_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Purchase Completed At",
                help_text="When purchase was completed",
            ),
        ),
        migrations.AddField(
            model_name="pipeline",
            name="in_production_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="In Production At",
                help_text="When production stage started",
            ),
        ),
        migrations.AddField(
            model_name="pipeline",
            name="production_completed_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Production Completed At",
                help_text="When production was completed",
            ),
        ),
        migrations.AddField(
            model_name="pipeline",
            name="in_purchase_and_production_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="In Purchase And Production At",
                help_text="When combined purchase+production stage started",
            ),
        ),
        migrations.AddField(
            model_name="pipeline",
            name="purchase_and_production_completed_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Purchase And Production Completed At",
                help_text="When combined purchase+production was completed",
            ),
        ),
        migrations.AddField(
            model_name="pipeline",
            name="in_outbound_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="In Outbound At",
                help_text="When outbound process started",
            ),
        ),
        migrations.AddField(
            model_name="pipeline",
            name="outbound_completed_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Outbound Completed At",
                help_text="When outbound was completed",
            ),
        ),
    ]
