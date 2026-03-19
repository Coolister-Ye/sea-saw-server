import os
import uuid

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..metadata import CustomMetadata
from ..models import DownloadTask
from ..pagination import CustomPageNumberPagination
from ..permissions import IsTaskOwner
from ..serializers import DownloadTaskSerializer
from ..tasks import generate_csv_task
from ..utilis import dynamic_import_model


class DownloadView(APIView):
    """
    接收筛选条件并创建异步 CSV 下载任务的基类视图。
    子类需要提供 download_obj_mapping 以声明支持的模型和序列化器。
    """

    permission_classes = [IsAuthenticated, DjangoModelPermissions]

    # 子类必须覆盖：{model_name: {"model": "app.Model", "serializer": "app.Serializer"}}
    download_obj_mapping = {}

    def _get_mapping(self, model_name):
        mapping = self.download_obj_mapping.get(model_name)
        if not mapping:
            raise ValueError(f"Unsupported model: {model_name}")
        return mapping

    def get_model_path(self, model_name):
        return self._get_mapping(model_name)["model"]

    def get_serializer_path(self, model_name):
        return self._get_mapping(model_name)["serializer"]

    def get_queryset(self):
        """Required by DjangoModelPermissions."""
        model_name = self.request.data.get("model")
        model_path = self.get_model_path(model_name)
        app_name, cls_name = model_path.split(".")
        model_class = dynamic_import_model(app_name, cls_name)
        return model_class.objects.all()

    def get_filters(self, request):
        return request.data.get("filter", {})

    def get_ordering(self, request):
        return request.data.get("ordering", [])

    def post(self, request):
        MAX_CONCURRENT_TASKS = 3
        user = request.user
        processing_count = DownloadTask.objects.filter(
            user=user,
            status=DownloadTask.Status.PROCESSING
        ).count()

        if processing_count >= MAX_CONCURRENT_TASKS:
            return Response(
                {
                    "error": f"您有太多正在处理的任务（{processing_count}/{MAX_CONCURRENT_TASKS}），请等待完成后再试",
                    "processing_tasks": processing_count,
                    "max_allowed": MAX_CONCURRENT_TASKS,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        model_name = request.data.get("model")
        if not model_name:
            return Response(
                {"detail": "model 字段为必填项。"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        model_path = self.get_model_path(model_name)
        serializer_path = self.get_serializer_path(model_name)
        filters = self.get_filters(request)
        ordering = self.get_ordering(request)

        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        file_uid = uuid.uuid4().hex
        file_name = f"{user.username}/{model_name}_{timestamp}_{file_uid}.csv"
        file_path = os.path.join(settings.MEDIA_ROOT, "downloads", file_name)

        task = DownloadTask.objects.create(
            user=user,
            file_name=file_name,
            file_path=file_path,
            status=DownloadTask.Status.PROCESSING,
        )

        task_json = DownloadTaskSerializer(task).data

        generate_csv_task.delay_on_commit(
            model_path, serializer_path, filters, ordering, task_json
        )

        return Response(
            {"task_id": task.id, "message": "下载任务已创建。"},
            status=status.HTTP_202_ACCEPTED,
        )


class UserDownloadTasksView(ListAPIView):
    """
    获取当前用户的所有下载任务。

    查询参数：
    - include_deleted=true: 包含已软删除的任务
    """

    permission_classes = [IsAuthenticated, IsTaskOwner]
    queryset = DownloadTask.objects.all()
    serializer_class = DownloadTaskSerializer
    metadata_class = CustomMetadata
    pagination_class = CustomPageNumberPagination
    filter_backends = (OrderingFilter,)
    ordering_fields = ["created_at"]

    def get_queryset(self):
        user = self.request.user
        include_deleted = self.request.query_params.get('include_deleted', 'false').lower() == 'true'

        if include_deleted:
            queryset = DownloadTask.all_objects.all()
        else:
            queryset = DownloadTask.objects.all()

        return queryset.filter(user=user)
