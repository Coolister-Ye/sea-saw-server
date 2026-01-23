from rest_framework import serializers

from .models import DownloadTask


class DownloadTaskSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)
    progress_percentage = serializers.IntegerField(read_only=True)  # 进度百分比

    class Meta:
        model = DownloadTask
        fields = [
            "pk",
            "user",
            "task_id",
            "file_name",
            "file_path",
            "download_url",
            "status",
            "created_at",
            "completed_at",
            "expires_at",
            "deleted",  # SafeDeleteModel 自动提供的删除时间字段
            "total_records",
            "processed_records",
            "progress_percentage",
            "error_message",
        ]
        read_only_fields = [
            "pk",
            "user",
            "task_id",
            "file_name",
            "file_path",
            "download_url",
            "status",
            "created_at",
            "completed_at",
            "expires_at",
            "deleted",
            "total_records",
            "processed_records",
            "progress_percentage",
            "error_message",
        ]
