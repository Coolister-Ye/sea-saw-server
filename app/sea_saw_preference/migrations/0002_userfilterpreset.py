import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sea_saw_preference", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserFilterPreset",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("entity", models.CharField(max_length=100, verbose_name="Entity")),
                ("name", models.CharField(max_length=100, verbose_name="Preset name")),
                (
                    "key",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=100,
                        verbose_name="Key",
                    ),
                ),
                ("params", models.JSONField(verbose_name="Filter params")),
                (
                    "preset_type",
                    models.CharField(
                        choices=[("system", "System"), ("user", "User")],
                        default="user",
                        max_length=10,
                        verbose_name="Preset type",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when this object was created.",
                        verbose_name="Created At",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when this object was last updated.",
                        verbose_name="Updated At",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="User",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="userfilterpreset",
            constraint=models.UniqueConstraint(
                condition=models.Q(preset_type="user"),
                fields=["user", "entity", "name"],
                name="unique_user_entity_preset_name",
            ),
        ),
        migrations.AddConstraint(
            model_name="userfilterpreset",
            constraint=models.UniqueConstraint(
                condition=models.Q(preset_type="system"),
                fields=["entity", "key"],
                name="unique_system_entity_key",
            ),
        ),
    ]
