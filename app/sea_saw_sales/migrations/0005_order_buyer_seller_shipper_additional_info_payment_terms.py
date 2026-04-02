from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("sea_saw_crm", "0001_initial"),
        ("sea_saw_sales", "0004_add_bank_account_fk"),
    ]

    operations = [
        # Remove the old index on 'account' before renaming the field
        migrations.RemoveIndex(
            model_name="order",
            name="sea_saw_sal_account_77370b_idx",
        ),
        # Rename account -> buyer
        migrations.RenameField(
            model_name="order",
            old_name="account",
            new_name="buyer",
        ),
        # Update related_name on buyer (requires AlterField)
        migrations.AlterField(
            model_name="order",
            name="buyer",
            field=models.ForeignKey(
                blank=True,
                help_text="Buyer account for this order",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="buyer_orders",
                to="sea_saw_crm.account",
                verbose_name="Buyer",
            ),
        ),
        # Add seller
        migrations.AddField(
            model_name="order",
            name="seller",
            field=models.ForeignKey(
                blank=True,
                help_text="Seller account for this order",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="seller_orders",
                to="sea_saw_crm.account",
                verbose_name="Seller",
            ),
        ),
        # Add shipper
        migrations.AddField(
            model_name="order",
            name="shipper",
            field=models.ForeignKey(
                blank=True,
                help_text="Shipper account for this order",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="shipper_orders",
                to="sea_saw_crm.account",
                verbose_name="Shipper",
            ),
        ),
        # Add additional_info
        migrations.AddField(
            model_name="order",
            name="additional_info",
            field=models.TextField(
                blank=True,
                help_text="Additional information for PI template",
                null=True,
                verbose_name="Additional Info",
            ),
        ),
        # Add payment_terms
        migrations.AddField(
            model_name="order",
            name="payment_terms",
            field=models.TextField(
                blank=True,
                help_text="Free-text payment terms (overrides deposit/balance format if set)",
                null=True,
                verbose_name="Term/Method of Payment",
            ),
        ),
        # Re-add the index on the renamed field 'buyer'
        migrations.AddIndex(
            model_name="order",
            index=models.Index(fields=["buyer"], name="sea_saw_sal_buyer_idx"),
        ),
    ]
