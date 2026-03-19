import logging
import os
from datetime import timedelta

import pandas as pd
from celery import shared_task
from django.conf import settings
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import activate

from sea_saw_download.models import DownloadTask
from sea_saw_download.utilis import dynamic_import_model, flatten, dynamic_import_serializer

logger = logging.getLogger(__name__)


def split_class_path(class_path):
    """Split 'app_name.ClassName' into (app_name, class_name)."""
    app_name, class_name = class_path.split(".")
    return app_name, class_name


@shared_task(bind=True)
def generate_csv_task(self, model_cls, serializer_cls, filters, ordering, task):
    """
    Generate a CSV file for the filtered data using pandas with chunked processing.
    Processes data in chunks to avoid memory issues with large datasets.
    """
    activate("zh-hans")

    task_obj = get_object_or_404(DownloadTask, pk=task["pk"])

    try:
        app_name, model_name = split_class_path(model_cls)
        model = dynamic_import_model(app_name, model_name)

        app_name, serializer_name = split_class_path(serializer_cls)
        serializer = dynamic_import_serializer(app_name, serializer_name)

        total_count = model.objects.filter(**filters).count()
        task_obj.total_records = total_count
        task_obj.save()

        MAX_RECORDS = 100000
        if total_count > MAX_RECORDS:
            task_obj.status = DownloadTask.Status.FAILED
            task_obj.error_message = (
                f"数据量过大（{total_count:,} 条记录），请缩小筛选范围至 {MAX_RECORDS:,} 条以内"
            )
            task_obj.save()
            return {"error": task_obj.error_message}

        directory = os.path.dirname(task["file_path"])
        os.makedirs(directory, exist_ok=True)

    except Exception as e:
        task_obj.status = DownloadTask.Status.FAILED
        task_obj.error_message = str(e)
        task_obj.save()
        return {"error": str(e)}

    try:
        CHUNK_SIZE = 1000
        first_chunk = True

        for offset in range(0, total_count, CHUNK_SIZE):
            task_obj.processed_records = offset
            task_obj.save()

            self.update_state(
                state='PROGRESS',
                meta={
                    'current': offset,
                    'total': total_count,
                    'percentage': int((offset / total_count) * 100) if total_count > 0 else 0
                }
            )

            queryset = model.objects.filter(**filters).order_by(*ordering)[offset:offset + CHUNK_SIZE]
            data, headers = flatten(queryset, serializer)

            df = pd.DataFrame.from_records(data)
            df = df.rename(columns=headers)
            df.to_csv(
                task["file_path"],
                mode='a',
                header=first_chunk,
                index=False,
                encoding="utf-8-sig"
            )
            first_chunk = False

        task_obj.status = DownloadTask.Status.COMPLETED
        task_obj.completed_at = timezone.now()
        task_obj.processed_records = total_count
        task_obj.expires_at = timezone.now() + timedelta(days=7)
        task_obj.download_url = (
            f"{settings.MEDIA_URL.rstrip('/')}/downloads/{task_obj.file_name}"
        )
        task_obj.save()

        return task_obj.pk

    except Exception as e:
        task_obj.status = DownloadTask.Status.FAILED
        task_obj.error_message = str(e)
        task_obj.save()
        return {"error": str(e)}


@shared_task
def cleanup_expired_downloads():
    """
    定时清理过期的下载文件（每天凌晨2点执行）

    使用 django-safedelete 的软删除功能：
    - 调用 delete() 会软删除（标记 deleted 字段）
    - 默认查询自动过滤已删除对象
    - 可通过 all_objects 访问所有对象
    """
    now = timezone.now()
    expiry_date = now - timedelta(days=7)

    expired_tasks = DownloadTask.objects.filter(
        status=DownloadTask.Status.COMPLETED
    ).filter(
        models.Q(expires_at__lt=now) | models.Q(expires_at__isnull=True, created_at__lt=expiry_date)
    )

    deleted_count = 0
    freed_space = 0

    for task in expired_tasks:
        if task.file_path and os.path.exists(task.file_path):
            try:
                freed_space += os.path.getsize(task.file_path)
                os.remove(task.file_path)
            except Exception as e:
                logger.warning("Failed to delete file %s: %s", task.file_path, e)

        task.download_url = None
        task.save()
        task.delete()
        deleted_count += 1

    _cleanup_empty_directories()

    freed_mb = round(freed_space / (1024 * 1024), 2)
    logger.info("Cleaned up %d expired download tasks, freed %s MB", deleted_count, freed_mb)
    return {
        'deleted_tasks': deleted_count,
        'freed_space_mb': freed_mb,
        'message': f'成功清理 {deleted_count} 个过期下载任务，释放 {freed_mb} MB 空间'
    }


def _cleanup_empty_directories():
    """清理空的用户下载目录"""
    downloads_dir = os.path.join(settings.MEDIA_ROOT, 'downloads')

    if not os.path.exists(downloads_dir):
        return

    for username in os.listdir(downloads_dir):
        user_dir = os.path.join(downloads_dir, username)
        if os.path.isdir(user_dir) and not os.listdir(user_dir):
            try:
                os.rmdir(user_dir)
            except Exception as e:
                logger.warning("Failed to remove empty directory %s: %s", user_dir, e)
