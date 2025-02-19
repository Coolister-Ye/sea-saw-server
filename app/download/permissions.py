from rest_framework.permissions import BasePermission

<<<<<<< HEAD

=======
>>>>>>> b8ed2530b8fff5b07d0c432a841b3ffb83230787
class IsTaskOwner(BasePermission):
    """
    只允许任务的所有者访问该任务
    """
<<<<<<< HEAD

=======
>>>>>>> b8ed2530b8fff5b07d0c432a841b3ffb83230787
    def has_object_permission(self, request, view, obj):
        # 确保只有任务的所有者才能访问
        return obj.user == request.user
