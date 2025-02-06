# Generated by Django 5.1.2 on 2025-02-05 07:57

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('download', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='downloadtask',
            name='created_at',
        ),
        migrations.AddField(
            model_name='downloadtask',
            name='download_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='downloadtask',
            name='error_message',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='downloadtask',
            name='file_path',
            field=models.CharField(max_length=1024),
        ),
        migrations.AlterField(
            model_name='downloadtask',
            name='status',
            field=models.CharField(default='processing', max_length=50),
        ),
        migrations.AlterField(
            model_name='downloadtask',
            name='task_id',
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='downloadtask',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
