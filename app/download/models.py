from django.db import models

from sea_saw_auth.models import User


class DownloadTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="download_tasks")
    task_id = models.CharField(max_length=255, unique=True)
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=1024)  # Path where the file is saved
    status = models.CharField(max_length=50, default="processing")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    download_url = models.URLField(null=True, blank=True)  # Add this field for the download URL

    def __str__(self):
        return f"Download task {self.task_id} for {self.file_name}"
