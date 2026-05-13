import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sea_saw_auth", "0001_initial"),
        ("sea_saw_preference", "0002_userfilterpreset"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.DeleteModel(name="UserColumnPreference"),
        migrations.DeleteModel(name="UserFilterPreset"),
        migrations.CreateModel(
            name="CustomView",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("entity", models.CharField(max_length=100, verbose_name="Entity")),
                ("name", models.CharField(max_length=100, verbose_name="Name")),
                ("key", models.CharField(blank=True, default="", max_length=100, verbose_name="Key")),
                ("is_system", models.BooleanField(default=False, verbose_name="Is system")),
                ("params", models.JSONField(default=dict, verbose_name="Filter params")),
                (
                    "column_order",
                    models.JSONField(
                        default=list,
                        help_text="Ordered list of visible column field names. Empty list means use page default.",
                        verbose_name="Column order",
                    ),
                ),
                (
                    "visibility",
                    models.CharField(
                        choices=[("private", "Private"), ("shared", "Shared"), ("public", "Public")],
                        default="private",
                        max_length=10,
                        verbose_name="Visibility",
                    ),
                ),
                ("is_default", models.BooleanField(default=False, verbose_name="Is default")),
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
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="custom_views",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Owner",
                    ),
                ),
                (
                    "shared_roles",
                    models.ManyToManyField(
                        blank=True,
                        related_name="shared_custom_views",
                        to="sea_saw_auth.role",
                        verbose_name="Shared with roles",
                    ),
                ),
                (
                    "shared_users",
                    models.ManyToManyField(
                        blank=True,
                        related_name="shared_custom_views",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Shared with users",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="customview",
            constraint=models.UniqueConstraint(
                condition=models.Q(is_default=True, is_system=False),
                fields=["owner", "entity"],
                name="unique_default_view_per_owner_entity",
            ),
        ),
        migrations.AddConstraint(
            model_name="customview",
            constraint=models.UniqueConstraint(
                condition=models.Q(is_system=False),
                fields=["owner", "entity", "name"],
                name="unique_custom_view_name_per_owner_entity",
            ),
        ),
        migrations.AddConstraint(
            model_name="customview",
            constraint=models.UniqueConstraint(
                condition=models.Q(is_system=True),
                fields=["entity", "key"],
                name="unique_system_view_entity_key",
            ),
        ),
        migrations.AddIndex(
            model_name="customview",
            index=models.Index(fields=["entity", "visibility"], name="customview_entity_visibility_idx"),
        ),
        migrations.AddIndex(
            model_name="customview",
            index=models.Index(fields=["is_system"], name="customview_is_system_idx"),
        ),
    ]
