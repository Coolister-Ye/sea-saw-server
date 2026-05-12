from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission, SAFE_METHODS


class CanMutateCustomView(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if obj.is_system:
            raise PermissionDenied("System views cannot be modified or deleted.")
        if obj.owner != request.user and not request.user.is_staff:
            raise PermissionDenied("You can only modify your own views.")
        return True
