from django.contrib.auth.models import Group
from rest_framework import serializers

from sea_saw_auth.models import User, Role


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = "__all__"


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    """User Serializer"""

    role = RoleSerializer()
    groups = GroupSerializer(many=True)

    class Meta:
        model = User
        fields = "__all__"
