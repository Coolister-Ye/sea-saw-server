from rest_framework import serializers

from sea_saw_auth.models import Role, User
from sea_saw_preference.models import CustomView


class CustomViewSerializer(serializers.ModelSerializer):
    shared_users = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        required=False,
    )
    shared_roles = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Role.objects.all(),
        required=False,
    )
    shared_user_names = serializers.SerializerMethodField()
    shared_role_names = serializers.SerializerMethodField()
    owner_username = serializers.CharField(source="owner.username", read_only=True)
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = CustomView
        fields = [
            "id",
            "entity",
            "name",
            "key",
            "is_system",
            "params",
            "column_order",
            "visibility",
            "is_default",
            "shared_users",
            "shared_roles",
            "shared_user_names",
            "shared_role_names",
            "owner_username",
            "is_owner",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "key", "is_system", "owner_username", "is_owner", "created_at", "updated_at"]

    def get_is_owner(self, obj):
        request = self.context.get("request")
        return bool(request and obj.owner_id == request.user.id)

    def get_shared_user_names(self, obj):
        return [u.username for u in obj.shared_users.all()]

    def get_shared_role_names(self, obj):
        return [r.role_name for r in obj.shared_roles.all()]

    def validate(self, data):
        visibility = data.get("visibility", getattr(self.instance, "visibility", "private"))
        if visibility == CustomView.VisibilityChoice.PRIVATE:
            data["shared_users"] = []
            data["shared_roles"] = []
        return data
