import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sea_saw_procurement', '0004_alter_purchaseitem_glazing'),
        ('sea_saw_pipeline', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchaseorder',
            name='pipeline',
            field=models.ForeignKey(
                blank=True,
                null=True,
                help_text='The business process pipeline this purchase order belongs to.',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='purchase_orders',
                to='sea_saw_pipeline.pipeline',
                verbose_name='Pipeline',
            ),
        ),
    ]
