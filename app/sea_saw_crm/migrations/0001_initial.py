# Generated by Django 5.1 on 2024-11-04 06:55

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Company",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_by", models.CharField(blank=True, max_length=100, null=True)),
                ("updated_by", models.CharField(blank=True, max_length=100, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(blank=True, default=False, null=True)),
                ("company_name", models.CharField(max_length=255)),
                ("email", models.EmailField(blank=True, max_length=254, null=True)),
                ("mobile", models.CharField(blank=True, max_length=255, null=True)),
                ("phone", models.CharField(blank=True, max_length=255, null=True)),
                ("home_phone", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "owner",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="Contact",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_by", models.CharField(blank=True, max_length=100, null=True)),
                ("updated_by", models.CharField(blank=True, max_length=100, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(blank=True, default=False, null=True)),
                ("first_name", models.CharField(blank=True, max_length=255, null=True)),
                ("last_name", models.CharField(blank=True, max_length=255, null=True)),
                ("title", models.CharField(blank=True, max_length=255, null=True)),
                ("email", models.EmailField(blank=True, max_length=254, null=True, unique=True)),
                ("mobile", models.CharField(blank=True, max_length=255, null=True)),
                ("phone", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "owner",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["last_name"]},
        ),
        migrations.CreateModel(
            name="Deal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_by", models.CharField(blank=True, max_length=100, null=True)),
                ("updated_by", models.CharField(blank=True, max_length=100, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(blank=True, default=False, null=True)),
                ("deal_name", models.CharField(max_length=255)),
                ("amount", models.DecimalField(blank=True, decimal_places=5, max_digits=10, null=True)),
                ("expected_revenue", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("closing_date", models.DateTimeField()),
                ("description", models.TextField(blank=True, default="", null=True)),
                ("contact", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="sea_saw_crm.contact")),
                (
                    "owner",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="Contract",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_by", models.CharField(blank=True, max_length=100, null=True)),
                ("updated_by", models.CharField(blank=True, max_length=100, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(blank=True, default=False, null=True)),
                ("contract_code", models.CharField(max_length=255, verbose_name="合同编号")),
                ("contract_date", models.DateField(verbose_name="合同签订日期")),
                (
                    "owner",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "deal",
                    models.OneToOneField(
                        blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="sea_saw_crm.deal"
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="Field",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_by", models.CharField(blank=True, max_length=100, null=True)),
                ("updated_by", models.CharField(blank=True, max_length=100, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(blank=True, default=False, null=True)),
                ("field_name", models.CharField(max_length=255)),
                (
                    "field_type",
                    models.CharField(
                        choices=[
                            ("picklist", "Picklist"),
                            ("text", "Text"),
                            ("numerical", "Numerical"),
                            ("lookup", "Lookup"),
                            ("date", "Date"),
                            ("currency", "Currency"),
                            ("email", "Email"),
                            ("phone", "Phone"),
                            ("url", "URL"),
                        ],
                        default="text",
                        max_length=50,
                    ),
                ),
                (
                    "field_tag",
                    models.CharField(blank=True, help_text="Group fields together", max_length=255, null=True),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("is_mandatory", models.BooleanField(default=False)),
                ("extra_info", models.JSONField(blank=True, null=True)),
                (
                    "content_type",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="contenttypes.contenttype"),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["id"], "unique_together": {("content_type", "field_name")}},
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_by", models.CharField(blank=True, max_length=100, null=True)),
                ("updated_by", models.CharField(blank=True, max_length=100, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(blank=True, default=False, null=True)),
                ("order_code", models.CharField(blank=True, default="", max_length=100, verbose_name="生产编号")),
                ("etd", models.DateField(verbose_name="预计发货日期")),
                (
                    "deposit",
                    models.DecimalField(blank=True, decimal_places=5, max_digits=10, null=True, verbose_name="定金"),
                ),
                (
                    "balance",
                    models.DecimalField(blank=True, decimal_places=5, max_digits=10, null=True, verbose_name="余额"),
                ),
                ("destination_port", models.CharField(blank=True, max_length=100, null=True, verbose_name="目的港口")),
                (
                    "contract",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="orders", to="sea_saw_crm.contract"
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="OrderProduct",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_by", models.CharField(blank=True, max_length=100, null=True)),
                ("updated_by", models.CharField(blank=True, max_length=100, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(blank=True, default=False, null=True)),
                ("product_name", models.CharField(max_length=255, null=True, verbose_name="产品名称")),
                ("product_code", models.CharField(blank=True, max_length=255, null=True, verbose_name="产品代码")),
                ("product_type", models.CharField(blank=True, max_length=255, null=True, verbose_name="产品类型")),
                ("packaging", models.CharField(blank=True, max_length=255, null=True, verbose_name="包装类型")),
                ("size", models.CharField(blank=True, max_length=100, null=True, verbose_name="规格")),
                (
                    "glazing",
                    models.DecimalField(
                        blank=True, decimal_places=5, max_digits=10, null=True, verbose_name="冰衣服比例"
                    ),
                ),
                ("quantity", models.IntegerField(blank=True, null=True, verbose_name="数量")),
                (
                    "list_price",
                    models.DecimalField(blank=True, decimal_places=5, max_digits=10, null=True, verbose_name="价格"),
                ),
                (
                    "discount",
                    models.DecimalField(blank=True, decimal_places=5, max_digits=10, null=True, verbose_name="折扣"),
                ),
                ("progress_quantity", models.IntegerField(blank=True, null=True, verbose_name="进度数量")),
                ("is_available", models.BooleanField(default=True, verbose_name="是否生效")),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="products", to="sea_saw_crm.order"
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="Pipeline",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_by", models.CharField(blank=True, max_length=100, null=True)),
                ("updated_by", models.CharField(blank=True, max_length=100, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(blank=True, default=False, null=True)),
                ("pipeline_name", models.CharField(max_length=255)),
                (
                    "owner",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.AddField(
            model_name="deal",
            name="pipeline",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="sea_saw_crm.pipeline"
            ),
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_by", models.CharField(blank=True, max_length=100, null=True)),
                ("updated_by", models.CharField(blank=True, max_length=100, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(blank=True, default=False, null=True)),
                ("product_name", models.CharField(max_length=255, unique=True)),
                ("product_code", models.CharField(blank=True, max_length=255, null=True)),
                ("product_type", models.CharField(blank=True, max_length=255, null=True)),
                ("is_available", models.BooleanField(default=True)),
                (
                    "owner",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="Stage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_by", models.CharField(blank=True, max_length=100, null=True)),
                ("updated_by", models.CharField(blank=True, max_length=100, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(blank=True, default=False, null=True)),
                ("stage_name", models.CharField(max_length=255)),
                ("stage_sector", models.IntegerField(default=0, help_text="0: Open Stage; 1: Closed Stage")),
                ("stage_type", models.IntegerField(default=2, help_text="0: Fail; 1: Success; 2: Other")),
                (
                    "owner",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("pipeline", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="sea_saw_crm.pipeline")),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="CustomFieldValue",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("value", models.TextField(default="")),
                ("object_id", models.PositiveIntegerField()),
                (
                    "content_type",
                    models.ForeignKey(
                        null=True, on_delete=django.db.models.deletion.SET_NULL, to="contenttypes.contenttype"
                    ),
                ),
                ("field", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="sea_saw_crm.field")),
            ],
            options={"unique_together": {("field", "content_type", "object_id")}},
        ),
    ]
