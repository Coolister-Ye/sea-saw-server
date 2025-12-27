from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q

from django.utils.translation import gettext_lazy as _


class RoleType(models.TextChoices):
    ADMIN = "ADMIN", _("Admin")
    SALE = "SALE", _("Sales")
    PRODUCTION = "PRODUCTION", _("Production")
    WAREHOUSE = "WAREHOUSE", _("Warehouse")
    FINANCE = "FINANCE", _("Finance")
    UNKNOWN = "UNKNOWN", _("Unknown")


class Role(models.Model):
    """Role model: 实现层级关系，用于数据可见性控制"""

    role_name = models.CharField(max_length=100)
    role_type = models.CharField(
        max_length=20, choices=RoleType.choices, default=RoleType.UNKNOWN
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )
    is_peer_visible = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.role_name

    def get_all_descendants(self):
        """
        Retrieve all descendant roles using a single query.
        Avoid recursive DB hits.
        """
        # Use BFS / iterative approach
        descendants = set()
        queue = list(self.children.all())
        while queue:
            current = queue.pop(0)
            descendants.add(current.id)
            queue.extend(current.children.all())
        return Role.objects.filter(id__in=descendants)

    def get_all_parent_users(self):
        """
        Retrieve all parent users using a single query.
        Avoid recursive DB hits.
        """
        # Use BFS / iterative approach
        parents = set()
        queue = list(self.parent.all())
        while queue:
            current = queue.pop(0)
            parents.add(current.id)
            queue.extend(current.parent.all())
        return User.objects.filter(role__in=parents)


class User(AbstractUser):
    phone = models.CharField(max_length=20, null=True, blank=True)
    department = models.CharField(max_length=100, null=True, blank=True)
    role = models.ForeignKey(
        Role, on_delete=models.SET_NULL, null=True, related_name="users"
    )

    def get_all_visible_users(self):
        """
        Returns queryset of users visible to this user based on role hierarchy and peer visibility.
        """
        if not self.role:
            return User.objects.filter(id=self.id)

        # Descendants of current role
        descendant_roles = self.role.get_all_descendants()

        if self.role.is_peer_visible:
            # Include self role
            visible_roles = list(descendant_roles) + [self.role.id]
        else:
            visible_roles = list(descendant_roles)

        # Include self user always
        return User.objects.filter(
            Q(role__in=visible_roles) | Q(id=self.id)
        ).select_related("role")
