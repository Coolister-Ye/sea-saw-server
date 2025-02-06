from rest_framework import serializers
from .models import DownloadTask

class DownloadTaskSerializer(serializers.ModelSerializer):
    user = serializers.CharField(
        source="user.username",
        read_only=True,
    )

    class Meta:
        model = DownloadTask
        fields = ["pk", "user", "task_id", "file_name", "file_path", "download_url", "status", "created_at", "completed_at"]
        read_only_fields = ["pk", "user", "task_id", "file_name", "file_path", "download_url", "status", "created_at", "completed_at"]
