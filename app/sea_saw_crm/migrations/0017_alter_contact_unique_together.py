# Generated by Django 5.1.2 on 2025-02-27 08:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sea_saw_crm', '0016_alter_order_options_alter_orderproduct_options'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='contact',
            unique_together={('email', 'deleted')},
        ),
    ]
