import os
import uuid

from django.utils import timezone
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from sea_saw_server import settings
from .metadata import CustomMetadata
from .models import DownloadTask
from .pagination import CustomPageNumberPagination
from .permissions import IsTaskOwner
from .serializers import DownloadTaskSerializer
from .tasks import generate_csv_task
from .utilis import dynamic_import_model


class DownloadView(APIView):
    """
    接收筛选条件并生成下载任务的视图类
    该视图允许用户提交筛选条件，并通过异步任务生成对应数据的CSV文件。
    (View class to receive filter conditions and create download tasks for CSV generation)
    """

    # 使用自定义的权限类，确保用户具有适当的权限
    # (Use custom permission class to ensure the user has the appropriate permissions)
    permission_classes = [IsAuthenticated, DjangoModelPermissions]

    # 映射不同对象类型到相应的模型和序列化器, 需要被overwrite
    # (Map different object types to corresponding models and serializers, needs to be overwritten in subclass)
    download_obj_mapping = {}

    def get_model_path(self, model_name):
        """
        根据模型名称动态加载模型类 (Dynamically import model class based on model name)
        """
        if model_name not in self.download_obj_mapping:
            raise Exception(f"Fail to load model meta for {model_name}")

        model_path = self.download_obj_mapping.get(model_name).get("model")
        return model_path

    def get_serializer_path(self, model_name):
        """
        根据模型名称动态加载序列化器类 (Dynamically import serializer class based on model name)
        """
        if model_name not in self.download_obj_mapping:
            raise Exception(f"Fail to load serializer meta for {model_name}")

        serializer_path = self.download_obj_mapping.get(model_name).get("serializer")
        return serializer_path

    def get_queryset(self):
        """
        To use DjangoModelPermissions, this function must be implemented.
        """
        model_name = self.request.data.get("model")
        model_path = self.get_model_path(model_name)
        app_name, model_name = model_path.split(".")
        model_class = dynamic_import_model(app_name, model_name)
        return model_class.objects.all()

    def get_filters(self, request):
        """
        Subclasses can overwrite this method to adjust filtering logic (可以重写此方法以调整筛选逻辑)
        """
        return request.data.get("filter", {})

    def get_ordering(self, request):
        """
        Subclasses can overwrite this method to adjust ordering logic (可以重写此方法以调整排序逻辑)
        """
        return request.data.get("ordering", [])

    def post(self, request):
        """
        处理POST请求，创建下载任务。 (Handle POST request to create a download task)
        """
        model_name = request.data.get("model")
        if not model_name:
            return Response(
                {"detail": "Model name is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Dynamically load model and serializer classes
        model_path = self.get_model_path(model_name)
        serializer_path = self.get_serializer_path(model_name)

        # Get filters and ordering from request
        filters = self.get_filters(request)
        ordering = self.get_ordering(request)
        username = request.user.username

        # Generate a unique file name to avoid duplication
        task_id = uuid.uuid4().hex
        file_name = f"{username}/{model_name}_{timezone.now().strftime('%Y%m%d%H%M%S')}_{task_id}.csv"
        file_path = os.path.join(settings.MEDIA_ROOT, "downloads", file_name)

        # Create a new download task record in the database
        task = DownloadTask.objects.create(
            user=request.user,
            task_id=task_id,
            file_name=file_name,
            file_path=file_path,
            status="processing",
        )

        # Serialize task data for passing to async task
        task_json = DownloadTaskSerializer(task).data

        # Start the async task to generate the CSV file
        generate_csv_task.delay_on_commit(
            model_path, serializer_path, filters, ordering, task_json
        )

        # Return task ID to inform the user the task has been created
        return Response(
            {
                "task_id": task.id,  # Return the generated task ID
                "message": "The download task has been initiated.",  # Inform the user the task has been started
            },
            status=status.HTTP_202_ACCEPTED,
        )


class UserDownloadTasksView(ListAPIView):
    """
    获取当前用户的所有下载任务
    """

    permission_classes = [IsAuthenticated, IsTaskOwner]  # 确保只有认证的用户能访问
    queryset = DownloadTask.objects.all()
    serializer_class = DownloadTaskSerializer
    metadata_class = CustomMetadata
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        """
        返回用户创建的下载任务列表
        """
        user = self.request.user
        queryset = super().get_queryset()

        return queryset.filter(user=user)
