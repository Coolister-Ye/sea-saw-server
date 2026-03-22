from rest_framework.permissions import IsAuthenticated

from sea_saw_base.permissions import CustomDjangoModelPermission
from sea_saw_download.views import DownloadView


class DownloadTaskView(DownloadView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermission]

    download_obj_mapping = {
        "orders": {
            "model": "sea_saw_sales.Order",
            "serializer": "sea_saw_sales.OrderSerializerForDownload",
        },
    }

    def get_filters(self, request):
        filters = super().get_filters(request)
        user = request.user

        if user.is_superuser or user.is_staff:
            return filters

        user_groups = set(user.groups.values_list("name", flat=True))
        if "Production" in user_groups:
            return filters

        # 非管理员：仅返回可见用户的数据
        visible_user_pks = [u.pk for u in user.get_all_visible_users()]
        filters["owner__pk__in"] = visible_user_pks
        return filters
