from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("sea_saw_crm", "0002_add_bank_account"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="bankaccount",
            name="account_holder",
        ),
        migrations.RenameField(
            model_name="bankaccount",
            old_name="account",
            new_name="account_holder",
        ),
    ]
