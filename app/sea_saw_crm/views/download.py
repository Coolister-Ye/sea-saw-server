from download.views import DownloadView
from rest_framework.permissions import IsAuthenticated

from ..permissions import CustomDjangoModelPermission


class DownloadTaskView(DownloadView):
    # 使用自定义的权限类，确保用户具有适当的权限
    # Using custom permission class to ensure the user has appropriate permissions
    permission_classes = [IsAuthenticated, CustomDjangoModelPermission]

    # 映射不同对象类型到相应的模型和序列化器
    # Map different object types to corresponding models and serializers
    download_obj_mapping = {
        "contracts": {
            "model": "sea_saw_crm.Contract",
            "serializer": "sea_saw_crm.ContractSerializer",
        },
        "orders": {
            "model": "sea_saw_crm.Order",
            "serializer": "sea_saw_crm.OrderSerializer4Prod",
        },
    }

    def get_filters(self, request):
        """
        获取并根据用户角色动态修改筛选条件。
        Get and dynamically modify filter conditions based on user roles.
        """
        filters_dict = super().get_filters(request)  # 获取父类的 filters 字典
        # Get the filters dictionary from the parent class
        user = request.user
        user_groups = set(user.groups.values_list("name", flat=True))

        # 如果是匿名用户，返回空查询条件
        # If the user is anonymous, return empty filter conditions
        if user.is_anonymous:
            filters_dict["id__in"] = []  # 不返回任何记录，类似于 filters.none()
            return filters_dict

        # 如果是管理员或超级用户，返回所有数据的过滤条件
        # If the user is an admin or superuser, return all data's filter conditions
        if user.is_superuser or user.is_staff:
            return filters_dict

        if "Production" in user_groups:
            return filters_dict

        # 非管理员用户，基于用户的可见性权限来过滤
        # For non-admin users, filter based on their visibility permissions
        visible_users = user.get_all_visible_users()
        visible_users = [user.pk for user in visible_users]
        filters_dict["owner__pk__in"] = (
            visible_users  # 增加过滤条件，限制查询可见的用户
        )
        # Add filter condition to restrict query to visible users

        return filters_dict
