# Generated by Django 5.1.2 on 2025-01-20 07:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('sea_saw_crm', '0014_remove_company_is_deleted_remove_contact_is_deleted_and_more')]

    operations = [
        migrations.AlterField(
            model_name='contract',
            name='contact',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='sea_saw_crm.contact',
                verbose_name='Contact',
            ),
        ),
        migrations.AlterField(
            model_name='order',
            name='contract',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='orders',
                to='sea_saw_crm.contract',
                verbose_name='Associated Contract',
            ),
        ),
        migrations.AlterField(
            model_name='orderproduct',
            name='order',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='products',
                to='sea_saw_crm.order',
                verbose_name='Associated Order',
            ),
        ),
    ]
