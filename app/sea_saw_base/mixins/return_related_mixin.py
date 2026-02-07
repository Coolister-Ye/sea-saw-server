"""
ReturnRelatedMixin - 支持在 create/update 后返回关联对象数据

使用场景：
当前端从父资源入口进入，操作子资源后希望直接获取更新后的父资源数据，
避免额外的 API 调用。

使用方法：
1. ViewSet 继承此 mixin
2. 设置 `related_field_name` 属性，指定关联字段名（如 "order"）
3. 设置 `role_related_serializer_map` 字典，定义不同角色对应的 serializer
4. 前端调用时添加 query parameter: `?return_related=true`

示例：
    class PaymentRecordViewSet(ReturnRelatedMixin, ModelViewSet):
        related_field_name = "order"
        role_related_serializer_map = {
            "ADMIN": OrderSerializerForAdmin,
            "SALE": OrderSerializerForSales,
        }

    # 前端调用
    POST /api/payments/?return_related=true
    PUT /api/payments/123/?return_related=true
"""
from rest_framework.response import Response
from rest_framework import status


class ReturnRelatedMixin:
    """
    Mixin for returning related object data after create/update operations.
    """

    # 需要在具体 ViewSet 中设置的属性
    related_field_name = None  # 关联字段名，如 "order"
    role_related_serializer_map = {}  # 角色 -> Serializer 的映射

    def _get_related_serializer(self, related_obj):
        """根据用户角色获取关联对象的 serializer"""
        if not self.role_related_serializer_map:
            raise NotImplementedError(
                "Must define 'role_related_serializer_map' in ViewSet"
            )

        role = getattr(self.request.user.role, "role_type", None)
        serializer_class = self.role_related_serializer_map.get(role)

        if not serializer_class:
            # 如果没有找到对应角色的 serializer，使用第一个作为默认
            serializer_class = next(iter(self.role_related_serializer_map.values()))

        return serializer_class(related_obj, context={"request": self.request})

    def _should_return_related(self):
        """检查是否应该返回关联对象数据"""
        return (
            self.request.query_params.get("return_related", "false").lower() == "true"
        )

    def _get_related_object(self, instance):
        """获取关联对象"""
        if not self.related_field_name:
            raise NotImplementedError("Must define 'related_field_name' in ViewSet")

        related_obj = getattr(instance, self.related_field_name, None)
        return related_obj

    def create(self, request, *args, **kwargs):
        """重写 create 方法，支持返回关联对象数据"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        # 如果请求参数中有 return_related=true，返回关联对象数据
        if self._should_return_related():
            related_obj = self._get_related_object(serializer.instance)
            if related_obj:
                related_serializer = self._get_related_serializer(related_obj)
                return Response(
                    related_serializer.data,
                    status=status.HTTP_201_CREATED,
                    headers=headers,
                )

        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def update(self, request, *args, **kwargs):
        """重写 update 方法，支持返回关联对象数据"""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}

        # 如果请求参数中有 return_related=true，返回关联对象数据
        if self._should_return_related():
            related_obj = self._get_related_object(serializer.instance)
            if related_obj:
                related_serializer = self._get_related_serializer(related_obj)
                return Response(related_serializer.data)

        return Response(serializer.data)
