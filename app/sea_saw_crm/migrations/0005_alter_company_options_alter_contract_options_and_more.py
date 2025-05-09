# Generated by Django 5.1.2 on 2024-12-12 15:44

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('sea_saw_crm', '0004_orderproduct_custom_fields_alter_deal_contact_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='company',
            options={'ordering': ['-created_at'], 'verbose_name': 'Base Model', 'verbose_name_plural': 'Base Models'},
        ),
        migrations.AlterModelOptions(
            name='contract',
            options={'ordering': ['-created_at'], 'verbose_name': 'Base Model', 'verbose_name_plural': 'Base Models'},
        ),
        migrations.AlterModelOptions(
            name='deal',
            options={'ordering': ['-created_at'], 'verbose_name': 'Base Model', 'verbose_name_plural': 'Base Models'},
        ),
        migrations.AlterModelOptions(
            name='field', options={'ordering': ['id'], 'verbose_name': 'Field', 'verbose_name_plural': 'Fields'}
        ),
        migrations.AlterModelOptions(
            name='order',
            options={'ordering': ['-created_at'], 'verbose_name': 'Base Model', 'verbose_name_plural': 'Base Models'},
        ),
        migrations.AlterModelOptions(
            name='orderproduct',
            options={'ordering': ['-created_at'], 'verbose_name': 'Base Model', 'verbose_name_plural': 'Base Models'},
        ),
        migrations.AlterModelOptions(
            name='pipeline',
            options={'ordering': ['-created_at'], 'verbose_name': 'Base Model', 'verbose_name_plural': 'Base Models'},
        ),
        migrations.AlterModelOptions(
            name='product',
            options={'ordering': ['-created_at'], 'verbose_name': 'Base Model', 'verbose_name_plural': 'Base Models'},
        ),
        migrations.AlterModelOptions(
            name='stage',
            options={'ordering': ['-created_at'], 'verbose_name': 'Base Model', 'verbose_name_plural': 'Base Models'},
        ),
        migrations.RemoveField(model_name='field', name='field_tag'),
        migrations.AlterField(
            model_name='company',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True, help_text='Timestamp when this object was created.', verbose_name='Created At'
            ),
        ),
        migrations.AlterField(
            model_name='company',
            name='created_by',
            field=models.CharField(
                blank=True,
                help_text='The user who created this object.',
                max_length=100,
                null=True,
                verbose_name='Created By',
            ),
        ),
        migrations.AlterField(
            model_name='company',
            name='is_deleted',
            field=models.BooleanField(
                blank=True,
                default=False,
                help_text='Soft delete flag for marking this object as deleted.',
                null=True,
                verbose_name='Is Deleted',
            ),
        ),
        migrations.AlterField(
            model_name='company',
            name='owner',
            field=models.ForeignKey(
                help_text='The user who owns this object.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='%(class)s',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Owner',
            ),
        ),
        migrations.AlterField(
            model_name='company',
            name='updated_at',
            field=models.DateTimeField(
                auto_now=True, help_text='Timestamp when this object was last updated.', verbose_name='Updated At'
            ),
        ),
        migrations.AlterField(
            model_name='company',
            name='updated_by',
            field=models.CharField(
                blank=True,
                help_text='The user who last updated this object.',
                max_length=100,
                null=True,
                verbose_name='Updated By',
            ),
        ),
        migrations.AlterField(
            model_name='contact',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True, help_text='Timestamp when this object was created.', verbose_name='Created At'
            ),
        ),
        migrations.AlterField(
            model_name='contact',
            name='created_by',
            field=models.CharField(
                blank=True,
                help_text='The user who created this object.',
                max_length=100,
                null=True,
                verbose_name='Created By',
            ),
        ),
        migrations.AlterField(
            model_name='contact',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, unique=True, verbose_name='邮箱'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='first_name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='名字'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='is_deleted',
            field=models.BooleanField(
                blank=True,
                default=False,
                help_text='Soft delete flag for marking this object as deleted.',
                null=True,
                verbose_name='Is Deleted',
            ),
        ),
        migrations.AlterField(
            model_name='contact',
            name='last_name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='姓氏'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='mobile',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='座机号'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='owner',
            field=models.ForeignKey(
                help_text='The user who owns this object.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='%(class)s',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Owner',
            ),
        ),
        migrations.AlterField(
            model_name='contact',
            name='phone',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='手机号'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='title',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='职位'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='updated_at',
            field=models.DateTimeField(
                auto_now=True, help_text='Timestamp when this object was last updated.', verbose_name='Updated At'
            ),
        ),
        migrations.AlterField(
            model_name='contact',
            name='updated_by',
            field=models.CharField(
                blank=True,
                help_text='The user who last updated this object.',
                max_length=100,
                null=True,
                verbose_name='Updated By',
            ),
        ),
        migrations.AlterField(
            model_name='contract',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True, help_text='Timestamp when this object was created.', verbose_name='Created At'
            ),
        ),
        migrations.AlterField(
            model_name='contract',
            name='created_by',
            field=models.CharField(
                blank=True,
                help_text='The user who created this object.',
                max_length=100,
                null=True,
                verbose_name='Created By',
            ),
        ),
        migrations.AlterField(
            model_name='contract',
            name='is_deleted',
            field=models.BooleanField(
                blank=True,
                default=False,
                help_text='Soft delete flag for marking this object as deleted.',
                null=True,
                verbose_name='Is Deleted',
            ),
        ),
        migrations.AlterField(
            model_name='contract',
            name='owner',
            field=models.ForeignKey(
                help_text='The user who owns this object.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='%(class)s',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Owner',
            ),
        ),
        migrations.AlterField(
            model_name='contract',
            name='updated_at',
            field=models.DateTimeField(
                auto_now=True, help_text='Timestamp when this object was last updated.', verbose_name='Updated At'
            ),
        ),
        migrations.AlterField(
            model_name='contract',
            name='updated_by',
            field=models.CharField(
                blank=True,
                help_text='The user who last updated this object.',
                max_length=100,
                null=True,
                verbose_name='Updated By',
            ),
        ),
        migrations.AlterField(
            model_name='deal',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True, help_text='Timestamp when this object was created.', verbose_name='Created At'
            ),
        ),
        migrations.AlterField(
            model_name='deal',
            name='created_by',
            field=models.CharField(
                blank=True,
                help_text='The user who created this object.',
                max_length=100,
                null=True,
                verbose_name='Created By',
            ),
        ),
        migrations.AlterField(
            model_name='deal',
            name='is_deleted',
            field=models.BooleanField(
                blank=True,
                default=False,
                help_text='Soft delete flag for marking this object as deleted.',
                null=True,
                verbose_name='Is Deleted',
            ),
        ),
        migrations.AlterField(
            model_name='deal',
            name='owner',
            field=models.ForeignKey(
                help_text='The user who owns this object.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='%(class)s',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Owner',
            ),
        ),
        migrations.AlterField(
            model_name='deal',
            name='updated_at',
            field=models.DateTimeField(
                auto_now=True, help_text='Timestamp when this object was last updated.', verbose_name='Updated At'
            ),
        ),
        migrations.AlterField(
            model_name='deal',
            name='updated_by',
            field=models.CharField(
                blank=True,
                help_text='The user who last updated this object.',
                max_length=100,
                null=True,
                verbose_name='Updated By',
            ),
        ),
        migrations.AlterField(
            model_name='field',
            name='content_type',
            field=models.ForeignKey(
                help_text='The model associated with this field.',
                on_delete=django.db.models.deletion.CASCADE,
                to='contenttypes.contenttype',
                verbose_name='Content Type TTT',
            ),
        ),
        migrations.AlterField(
            model_name='field',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True, help_text='Timestamp when this object was created.', verbose_name='Created At'
            ),
        ),
        migrations.AlterField(
            model_name='field',
            name='created_by',
            field=models.CharField(
                blank=True,
                help_text='The user who created this object.',
                max_length=100,
                null=True,
                verbose_name='Created By',
            ),
        ),
        migrations.AlterField(
            model_name='field',
            name='extra_info',
            field=models.JSONField(
                blank=True,
                help_text='Additional metadata or configuration for the field.',
                null=True,
                verbose_name='Extra Information',
            ),
        ),
        migrations.AlterField(
            model_name='field',
            name='field_name',
            field=models.CharField(
                help_text='Name of the field (must be unique within the same content type).',
                max_length=255,
                verbose_name='Field Name',
            ),
        ),
        migrations.AlterField(
            model_name='field',
            name='field_type',
            field=models.CharField(
                choices=[
                    ('picklist', 'Picklist'),
                    ('text', 'Text'),
                    ('numerical', 'Numerical'),
                    ('lookup', 'Lookup'),
                    ('date', 'Date'),
                    ('currency', 'Currency'),
                    ('email', 'Email'),
                    ('phone', 'Phone'),
                    ('url', 'URL'),
                ],
                default='text',
                help_text='Type of the field (e.g., text, picklist).',
                max_length=50,
                verbose_name='Field Type',
            ),
        ),
        migrations.AlterField(
            model_name='field',
            name='is_active',
            field=models.BooleanField(
                default=True, help_text='Indicates whether the field is active.', verbose_name='Is Active'
            ),
        ),
        migrations.AlterField(
            model_name='field',
            name='is_deleted',
            field=models.BooleanField(
                blank=True,
                default=False,
                help_text='Soft delete flag for marking this object as deleted.',
                null=True,
                verbose_name='Is Deleted',
            ),
        ),
        migrations.AlterField(
            model_name='field',
            name='is_mandatory',
            field=models.BooleanField(
                default=False, help_text='Indicates whether the field is mandatory.', verbose_name='Is Mandatory'
            ),
        ),
        migrations.AlterField(
            model_name='field',
            name='owner',
            field=models.ForeignKey(
                help_text='The user who owns this object.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='%(class)s',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Owner',
            ),
        ),
        migrations.AlterField(
            model_name='field',
            name='updated_at',
            field=models.DateTimeField(
                auto_now=True, help_text='Timestamp when this object was last updated.', verbose_name='Updated At'
            ),
        ),
        migrations.AlterField(
            model_name='field',
            name='updated_by',
            field=models.CharField(
                blank=True,
                help_text='The user who last updated this object.',
                max_length=100,
                null=True,
                verbose_name='Updated By',
            ),
        ),
        migrations.AlterField(
            model_name='order',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True, help_text='Timestamp when this object was created.', verbose_name='Created At'
            ),
        ),
        migrations.AlterField(
            model_name='order',
            name='created_by',
            field=models.CharField(
                blank=True,
                help_text='The user who created this object.',
                max_length=100,
                null=True,
                verbose_name='Created By',
            ),
        ),
        migrations.AlterField(
            model_name='order',
            name='is_deleted',
            field=models.BooleanField(
                blank=True,
                default=False,
                help_text='Soft delete flag for marking this object as deleted.',
                null=True,
                verbose_name='Is Deleted',
            ),
        ),
        migrations.AlterField(
            model_name='order',
            name='owner',
            field=models.ForeignKey(
                help_text='The user who owns this object.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='%(class)s',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Owner',
            ),
        ),
        migrations.AlterField(
            model_name='order',
            name='updated_at',
            field=models.DateTimeField(
                auto_now=True, help_text='Timestamp when this object was last updated.', verbose_name='Updated At'
            ),
        ),
        migrations.AlterField(
            model_name='order',
            name='updated_by',
            field=models.CharField(
                blank=True,
                help_text='The user who last updated this object.',
                max_length=100,
                null=True,
                verbose_name='Updated By',
            ),
        ),
        migrations.AlterField(
            model_name='orderproduct',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True, help_text='Timestamp when this object was created.', verbose_name='Created At'
            ),
        ),
        migrations.AlterField(
            model_name='orderproduct',
            name='created_by',
            field=models.CharField(
                blank=True,
                help_text='The user who created this object.',
                max_length=100,
                null=True,
                verbose_name='Created By',
            ),
        ),
        migrations.AlterField(
            model_name='orderproduct',
            name='is_deleted',
            field=models.BooleanField(
                blank=True,
                default=False,
                help_text='Soft delete flag for marking this object as deleted.',
                null=True,
                verbose_name='Is Deleted',
            ),
        ),
        migrations.AlterField(
            model_name='orderproduct',
            name='owner',
            field=models.ForeignKey(
                help_text='The user who owns this object.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='%(class)s',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Owner',
            ),
        ),
        migrations.AlterField(
            model_name='orderproduct',
            name='product_name',
            field=models.CharField(max_length=255, verbose_name='产品名称'),
        ),
        migrations.AlterField(
            model_name='orderproduct',
            name='updated_at',
            field=models.DateTimeField(
                auto_now=True, help_text='Timestamp when this object was last updated.', verbose_name='Updated At'
            ),
        ),
        migrations.AlterField(
            model_name='orderproduct',
            name='updated_by',
            field=models.CharField(
                blank=True,
                help_text='The user who last updated this object.',
                max_length=100,
                null=True,
                verbose_name='Updated By',
            ),
        ),
        migrations.AlterField(
            model_name='pipeline',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True, help_text='Timestamp when this object was created.', verbose_name='Created At'
            ),
        ),
        migrations.AlterField(
            model_name='pipeline',
            name='created_by',
            field=models.CharField(
                blank=True,
                help_text='The user who created this object.',
                max_length=100,
                null=True,
                verbose_name='Created By',
            ),
        ),
        migrations.AlterField(
            model_name='pipeline',
            name='is_deleted',
            field=models.BooleanField(
                blank=True,
                default=False,
                help_text='Soft delete flag for marking this object as deleted.',
                null=True,
                verbose_name='Is Deleted',
            ),
        ),
        migrations.AlterField(
            model_name='pipeline',
            name='owner',
            field=models.ForeignKey(
                help_text='The user who owns this object.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='%(class)s',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Owner',
            ),
        ),
        migrations.AlterField(
            model_name='pipeline',
            name='updated_at',
            field=models.DateTimeField(
                auto_now=True, help_text='Timestamp when this object was last updated.', verbose_name='Updated At'
            ),
        ),
        migrations.AlterField(
            model_name='pipeline',
            name='updated_by',
            field=models.CharField(
                blank=True,
                help_text='The user who last updated this object.',
                max_length=100,
                null=True,
                verbose_name='Updated By',
            ),
        ),
        migrations.AlterField(
            model_name='product',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True, help_text='Timestamp when this object was created.', verbose_name='Created At'
            ),
        ),
        migrations.AlterField(
            model_name='product',
            name='created_by',
            field=models.CharField(
                blank=True,
                help_text='The user who created this object.',
                max_length=100,
                null=True,
                verbose_name='Created By',
            ),
        ),
        migrations.AlterField(
            model_name='product',
            name='is_deleted',
            field=models.BooleanField(
                blank=True,
                default=False,
                help_text='Soft delete flag for marking this object as deleted.',
                null=True,
                verbose_name='Is Deleted',
            ),
        ),
        migrations.AlterField(
            model_name='product',
            name='owner',
            field=models.ForeignKey(
                help_text='The user who owns this object.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='%(class)s',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Owner',
            ),
        ),
        migrations.AlterField(
            model_name='product',
            name='updated_at',
            field=models.DateTimeField(
                auto_now=True, help_text='Timestamp when this object was last updated.', verbose_name='Updated At'
            ),
        ),
        migrations.AlterField(
            model_name='product',
            name='updated_by',
            field=models.CharField(
                blank=True,
                help_text='The user who last updated this object.',
                max_length=100,
                null=True,
                verbose_name='Updated By',
            ),
        ),
        migrations.AlterField(
            model_name='stage',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True, help_text='Timestamp when this object was created.', verbose_name='Created At'
            ),
        ),
        migrations.AlterField(
            model_name='stage',
            name='created_by',
            field=models.CharField(
                blank=True,
                help_text='The user who created this object.',
                max_length=100,
                null=True,
                verbose_name='Created By',
            ),
        ),
        migrations.AlterField(
            model_name='stage',
            name='is_deleted',
            field=models.BooleanField(
                blank=True,
                default=False,
                help_text='Soft delete flag for marking this object as deleted.',
                null=True,
                verbose_name='Is Deleted',
            ),
        ),
        migrations.AlterField(
            model_name='stage',
            name='owner',
            field=models.ForeignKey(
                help_text='The user who owns this object.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='%(class)s',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Owner',
            ),
        ),
        migrations.AlterField(
            model_name='stage',
            name='updated_at',
            field=models.DateTimeField(
                auto_now=True, help_text='Timestamp when this object was last updated.', verbose_name='Updated At'
            ),
        ),
        migrations.AlterField(
            model_name='stage',
            name='updated_by',
            field=models.CharField(
                blank=True,
                help_text='The user who last updated this object.',
                max_length=100,
                null=True,
                verbose_name='Updated By',
            ),
        ),
        migrations.AddConstraint(
            model_name='field',
            constraint=models.UniqueConstraint(
                fields=('content_type', 'field_name'), name='unique_field_per_content_type'
            ),
        ),
    ]
