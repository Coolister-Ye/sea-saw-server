from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("sea_saw_pipeline", "0001_initial"),
        ("sea_saw_warehouse", "0003_alter_outbounditem_glazing"),
    ]

    operations = [
        migrations.AlterField(
            model_name="outboundorder",
            name="pipeline",
            field=models.ForeignKey(
                blank=True,
                help_text="The business process pipeline this outbound order belongs to.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="outbound_orders",
                to="sea_saw_pipeline.pipeline",
                verbose_name="Pipeline",
            ),
        ),
    ]
