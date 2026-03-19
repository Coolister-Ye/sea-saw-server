from django.db import migrations


CONTENT_TYPE_TO_PAYMENT_TYPE = {
    "order": "order_payment",
    "purchaseorder": "purchase_payment",
    "productionorder": "production_payment",
    "outboundorder": "outbound_payment",
}


def fix_payment_types(apps, schema_editor):
    Payment = apps.get_model("sea_saw_finance", "Payment")

    payments = Payment.objects.select_related("content_type").exclude(content_type=None)
    for payment in payments:
        model_name = payment.content_type.model
        correct_type = CONTENT_TYPE_TO_PAYMENT_TYPE.get(model_name)
        if correct_type and payment.payment_type != correct_type:
            payment.payment_type = correct_type
            payment.save(update_fields=["payment_type"])


class Migration(migrations.Migration):

    dependencies = [
        ("sea_saw_finance", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(fix_payment_types, migrations.RunPython.noop),
    ]
