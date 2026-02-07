import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from safedelete.models import SafeDeleteModel, SOFT_DELETE_CASCADE

from sea_saw_auth.models import User


class DownloadTask(SafeDeleteModel):
    """
    下载任务模型 - 使用 django-safedelete 实现软删除

    软删除策略：SOFT_DELETE_CASCADE
    - 删除时不会从数据库中移除，而是标记 deleted 字段
    - 默认查询会自动过滤已删除对象
    - 可通过 all_objects 管理器访问所有对象（包括已删除）
    - 可通过 undelete() 方法恢复已删除对象
    """
    _safedelete_policy = SOFT_DELETE_CASCADE

    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        PROCESSING = 'processing', _('Processing')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="download_tasks")
    task_id = models.CharField(max_length=255, unique=True, blank=True)
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=1024)  # Path where the file is saved
    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.PROCESSING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    download_url = models.URLField(null=True, blank=True)  # Add this field for the download URL
    expires_at = models.DateTimeField(null=True, blank=True)  # 文件过期时间（7天后自动删除）
    total_records = models.IntegerField(null=True, blank=True)  # 总记录数
    processed_records = models.IntegerField(default=0)  # 已处理记录数

    def save(self, *args, **kwargs):
        """重写 save 方法，自动生成 task_id"""
        if not self.task_id:
            self.task_id = self._generate_task_id()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_task_id():
        """生成唯一的 task_id"""
        return str(uuid.uuid4())

    def __str__(self):
        return f"Download task {self.task_id} for {self.file_name}"

    @property
    def progress_percentage(self):
        """计算处理进度百分比"""
        if self.total_records and self.total_records > 0:
            return int((self.processed_records / self.total_records) * 100)
        return 0
