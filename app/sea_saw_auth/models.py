from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q


class Role(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    is_peer_visible = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

    def get_descendant_ids(self):
        """
        Retrieve all descendant role IDs recursively.
        """
        descendant_ids = list(self.children.values_list('id', flat=True))
        for child_id in descendant_ids[:]:
            child_role = Role.objects.get(id=child_id)
            descendant_ids.extend(child_role.get_descendant_ids())
        return descendant_ids

    def get_all_descendants(self):
        """
        Retrieve all descendant roles efficiently.
        """
        return Role.objects.filter(id__in=self.get_descendant_ids())


class User(AbstractUser):
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, related_name='users')

    def get_all_visible_users(self):
        if not self.role:
            return User.objects.filter(id=self.id)

        visible_roles = list(self.role.get_all_descendants())
        if self.role.is_peer_visible:
            visible_roles.append(self.role)
            return User.objects.filter(role__in=visible_roles).select_related('role')

        return User.objects.filter(Q(role__in=visible_roles) | Q(id=self.id)).select_related('role')
