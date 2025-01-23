from django.contrib import admin
from .models import User, Role
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin


class UserAdmin(DefaultUserAdmin):
    # 在列表视图中显示 'role'
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')

    # 在用户编辑界面中添加 'role' 字段
    fieldsets = DefaultUserAdmin.fieldsets + (
        (None, {'fields': ('role',)}),
    )


class RoleAdmin(admin.ModelAdmin):
    pass


admin.site.register(User, UserAdmin)
admin.site.register(Role, RoleAdmin)