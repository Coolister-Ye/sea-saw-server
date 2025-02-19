# Generated by Django 5.1.2 on 2024-12-20 14:55

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('sea_saw_crm', '0006_alter_company_options_alter_contact_options_and_more')]

    operations = [
        migrations.AlterModelOptions(
            name='orderproduct', options={'verbose_name': 'Order Product', 'verbose_name_plural': 'Order Products'}
        ),
        migrations.AddField(
            model_name='contact',
            name='full_name',
            field=models.CharField(
                blank=True,
                help_text="The contact's full name. Can be empty.",
                max_length=510,
                null=True,
                verbose_name='Full Name',
            ),
        ),
    ]
