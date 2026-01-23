import csv
import os
import pandas as pd
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import activate

from download.models import DownloadTask
from download.utilis import dynamic_import_model, flatten, dynamic_import_serializer


def split_class_path(class_path):
    """
    Split the class path (e.g., 'app_name.model_name') into app_name and class_name.
    """
    app_name, class_name = class_path.split(".")
    return app_name, class_name


def create_directory(directory):
    """
    Create the directory if it does not exist.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)


@shared_task(bind=True)
def generate_csv_task(self, model_cls, serializer_cls, filters, ordering, task):
    """
    Generate a CSV file for the filtered data using pandas with chunked processing.
    This prevents memory issues with large datasets.
    """
    activate("zh-hans")

    # Retrieve the model dynamically
    app_name, model_name = split_class_path(model_cls)
    model = dynamic_import_model(app_name, model_name)

    # Retrieve the serializer dynamically
    app_name, serializer_name = split_class_path(serializer_cls)
    serializer = dynamic_import_serializer(app_name, serializer_name)

    # Count total records
    total_count = model.objects.filter(**filters).count()

    # Update task with total count
    task_obj = get_object_or_404(DownloadTask, pk=task["pk"])
    task_obj.total_records = total_count
    task_obj.save()

    # Check data limit (100,000 records max)
    MAX_RECORDS = 100000
    if total_count > MAX_RECORDS:
        task_obj.status = DownloadTask.Status.FAILED
        task_obj.error_message = f"数据量过大（{total_count:,} 条记录），请缩小筛选范围至 {MAX_RECORDS:,} 条以内"
        task_obj.save()
        return {"error": task_obj.error_message}

    # Ensure the directory exists for the file path
    directory = os.path.dirname(task["file_path"])
    create_directory(directory)

    try:
        # Process data in chunks to avoid memory issues
        CHUNK_SIZE = 1000
        first_chunk = True

        for offset in range(0, total_count, CHUNK_SIZE):
            # Update progress
            task_obj.processed_records = offset
            task_obj.save()

            # Update Celery task state for real-time progress tracking
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': offset,
                    'total': total_count,
                    'percentage': int((offset / total_count) * 100) if total_count > 0 else 0
                }
            )

            # Query chunk of data
            queryset = model.objects.filter(**filters).order_by(*ordering)[offset:offset + CHUNK_SIZE]

            # Flatten the queryset and get the headers for CSV
            data, headers = flatten(queryset, serializer)

            # Convert data to pandas DataFrame
            df = pd.DataFrame.from_records(data)
            df = df.rename(columns=headers)

            # Write to CSV (append mode for all chunks except first)
            df.to_csv(
                task["file_path"],
                mode='a',  # Append mode
                header=first_chunk,  # Only write header on first chunk
                index=False,
                encoding="utf-8-sig"
            )
            first_chunk = False

        # Update the task status to 'completed' after successful file generation
        task_obj.status = DownloadTask.Status.COMPLETED
        task_obj.completed_at = timezone.now()
        task_obj.processed_records = total_count
        task_obj.expires_at = timezone.now() + timedelta(days=7)  # 7天后过期
        task_obj.download_url = os.path.join(
            settings.MEDIA_URL, "downloads", task_obj.file_name
        )
        task_obj.save()

        return task_obj.pk

    except Exception as e:
        # If an error occurs during the process, set the task status to 'failed'
        task_obj.status = DownloadTask.Status.FAILED
        task_obj.error_message = str(e)
        task_obj.save()

        return {"error": str(e)}


@shared_task
def cleanup_expired_downloads():
    """
    定时清理过期的下载文件（每天凌晨2点执行）
    删除已过期或创建超过7天的文件

    使用 django-safedelete 的软删除功能：
    - 调用 delete() 会软删除（标记 deleted 字段）
    - 默认查询自动过滤已删除对象
    - 可通过 all_objects 访问所有对象
    """
    from datetime import timedelta

    now = timezone.now()
    expiry_date = now - timedelta(days=7)

    # 查找过期任务（通过 expires_at 或 created_at）
    # 注意：DownloadTask.objects 已自动过滤已删除的对象
    expired_tasks = DownloadTask.objects.filter(
        status=DownloadTask.Status.COMPLETED
    ).filter(
        # 条件1: 有明确过期时间且已过期
        # 条件2: 或者创建时间超过7天（兜底逻辑）
        models.Q(expires_at__lt=now) | models.Q(created_at__lt=expiry_date, expires_at__isnull=True)
    )

    deleted_count = 0
    freed_space = 0

    for task in expired_tasks:
        # 删除物理文件
        if task.file_path and os.path.exists(task.file_path):
            try:
                file_size = os.path.getsize(task.file_path)
                os.remove(task.file_path)
                freed_space += file_size
            except Exception as e:
                # 记录错误但继续处理其他文件
                print(f"Failed to delete file {task.file_path}: {e}")

        # 清空下载链接并软删除任务
        task.download_url = None
        task.save()
        task.delete()  # 软删除（由 SafeDeleteModel 提供）
        deleted_count += 1

    # 清理空目录
    cleanup_empty_directories()

    return {
        'deleted_tasks': deleted_count,
        'freed_space_mb': round(freed_space / (1024 * 1024), 2),
        'message': f'成功清理 {deleted_count} 个过期下载任务，释放 {round(freed_space / (1024 * 1024), 2)} MB 空间'
    }


def cleanup_empty_directories():
    """
    清理空的用户下载目录
    """
    downloads_dir = os.path.join(settings.MEDIA_ROOT, 'downloads')

    if not os.path.exists(downloads_dir):
        return

    # 遍历用户目录
    for username in os.listdir(downloads_dir):
        user_dir = os.path.join(downloads_dir, username)

        if os.path.isdir(user_dir) and not os.listdir(user_dir):
            try:
                os.rmdir(user_dir)
            except Exception as e:
                print(f"Failed to remove empty directory {user_dir}: {e}")
