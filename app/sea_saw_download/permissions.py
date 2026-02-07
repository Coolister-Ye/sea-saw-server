from rest_framework.permissions import BasePermission


class IsTaskOwner(BasePermission):
    """
    只允许任务的所有者访问该任务
    """

    def has_object_permission(self, request, view, obj):
        # 确保只有任务的所有者才能访问
        return obj.user == request.user
