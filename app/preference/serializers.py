from rest_framework import serializers

from preference.models import UserColumnPreference


class UserColumnPreferenceSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username')

    class Meta:
        model = UserColumnPreference
        fields = ["user", "table_name", "column_pref", "created_at", "updated_at"]

    def create(self, validated_data):
        # 获取当前用户
        request = self.context.get('request')
        print("request.user", request.user)
        if request and request.user:
            validated_data["user"] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # 获取当前用户，防止覆盖已有的用户
        request = self.context.get('request')
        if request and request.user:
            validated_data["user"] = request.user
        return super().update(instance, validated_data)
