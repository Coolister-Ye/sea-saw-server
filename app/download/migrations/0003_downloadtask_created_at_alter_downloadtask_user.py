# Generated by Django 5.1.2 on 2025-02-05 08:01

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
<<<<<<< HEAD
=======

>>>>>>> b8ed2530b8fff5b07d0c432a841b3ffb83230787
    dependencies = [
        ('download', '0002_remove_downloadtask_created_at_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='downloadtask',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='downloadtask',
            name='user',
<<<<<<< HEAD
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name='download_tasks', to=settings.AUTH_USER_MODEL
            ),
=======
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='download_tasks', to=settings.AUTH_USER_MODEL),
>>>>>>> b8ed2530b8fff5b07d0c432a841b3ffb83230787
        ),
    ]
