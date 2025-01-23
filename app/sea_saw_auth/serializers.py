from django.contrib.auth.models import Group
from rest_framework import serializers

from sea_saw_auth.models import User, Role


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['pk', 'name']


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['pk', 'name']


class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer()
    groups = GroupSerializer(many=True)

    class Meta:
        model = User
        fields = ['pk', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'role', 'groups']
