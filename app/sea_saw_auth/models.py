from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    is_peer_visible = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

    def get_all_descendants(self):
        """
        Efficiently retrieve all descendants using a query rather than recursion.
        This avoids performance issues with deep recursion.
        """
        descendants = Role.objects.filter(id__in=self.get_descendant_ids())
        return descendants

    def get_descendant_ids(self):
        """Helper to get a flat list of IDs of all descendants."""
        descendants = list(self.children.all())
        all_ids = [child.id for child in descendants]

        # Loop over each child and add its descendants' IDs recursively
        for child in descendants:
            all_ids.extend(child.get_descendant_ids())

        return all_ids

    def get_peers(self):
        """
        Get all peer roles (roles with the same parent).
        """
        if not self.parent:
            return Role.objects.none()  # If no parent, no peers exist

        return Role.objects.filter(parent=self.parent).exclude(id=self.id)

    def get_all_visible_users(self):
        """
        Get all users visible to the current role:
        - Direct descendants
        - Peers (if `is_peer_visible` is True)
        """
        all_visible_roles = list(self.get_all_descendants())
        all_visible_roles.append(self)  # Include the current role

        if self.is_peer_visible:
            all_visible_roles.extend(self.get_peers())

        # Query the SeaSawUser model for users in the visible roles
        all_visible_users = User.objects.filter(role__in=all_visible_roles).select_related('role')

        return all_visible_users


class User(AbstractUser):
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, related_name='users')

    def get_all_visible_users(self):
        if self.role:
            return self.role.get_all_visible_users()
        return [self]
