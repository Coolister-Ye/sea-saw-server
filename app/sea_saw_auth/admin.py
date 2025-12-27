from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin

from .models import User, Role


@admin.register(User)
class UserAdmin(DefaultUserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "is_staff",
        "is_superuser",
        "is_active",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "role")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)

    # 编辑界面增加 role 字段
    fieldsets = DefaultUserAdmin.fieldsets + ((None, {"fields": ("role",)}),)

    # 如果 Role 数据量大，可以使用 raw_id_fields 或 autocomplete_fields 提升效率
    raw_id_fields = ("role",)
    # autocomplete_fields = ('role',)  # 需要在 RoleAdmin 中设置 search_fields


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("role_name", "role_type", "parent", "is_peer_visible")
    search_fields = ("role_name",)
    list_filter = ("is_peer_visible",)
