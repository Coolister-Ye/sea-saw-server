import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sea_saw_crm", "0003_bankaccount_rename_fields"),
        ("sea_saw_procurement", "0002_add_bank_account_fk"),
    ]

    operations = [
        migrations.AddField(
            model_name="purchaseorder",
            name="buyer",
            field=models.ForeignKey(
                blank=True,
                help_text="Buyer account for this purchase order",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="buyer_purchase_orders",
                to="sea_saw_crm.account",
                verbose_name="Buyer",
            ),
        ),
        migrations.AddField(
            model_name="purchaseorder",
            name="shipper",
            field=models.ForeignKey(
                blank=True,
                help_text="Shipper account for this purchase order",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="shipper_purchase_orders",
                to="sea_saw_crm.account",
                verbose_name="Shipper",
            ),
        ),
        migrations.AddField(
            model_name="purchaseorder",
            name="payment_terms",
            field=models.TextField(
                blank=True,
                help_text="Free-text payment terms.",
                null=True,
                verbose_name="Term/Method of Payment",
            ),
        ),
        migrations.AddField(
            model_name="purchaseorder",
            name="additional_info",
            field=models.TextField(
                blank=True,
                help_text="Additional information for document templates.",
                null=True,
                verbose_name="Additional Info",
            ),
        ),
    ]
