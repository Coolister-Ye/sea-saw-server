from copy import deepcopy
from rest_access_policy import AccessPolicy


class OrderAccessPolicyForProduction(AccessPolicy):
    """
    Production role access policy.

    - LIST / RETRIEVE / OPTIONS / HEAD: allowed if order is in a visible status
    - UPDATE / PARTIAL_UPDATE: allowed only when order is in IN_PRODUCTION or ORDER_CONFIRMED
    """

    statements = [
        {
            "action": ["list", "retrieve", "<method:options>", "<method:head>"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "is_production and is_order_visible",
        },
        {
            "action": ["update", "partial_update"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "is_production and is_editable",
        },
    ]

    # ------------------- 条件方法 -------------------

    def is_production(self, request, view, action):
        """是否 PRODUCTION 用户"""
        return getattr(request.user.role, "role_type", None) == "PRODUCTION"

    # 可见状态
    VISIBLE_STATUSES = {
        "ORDER_CONFIRMED",
        "IN_PRODUCTION",
        "PRODUCTION_COMPLETED",
        "IN_OUTBOUND",
        "OUTBOUND_COMPLETED",
        "COMPLETED",
        "CANCELLED",
        "ISSUE_REPORTED",
    }

    # 可编辑状态
    EDITABLE_STATUSES = {
        "ORDER_CONFIRMED",
        "IN_PRODUCTION",
    }

    def is_order_visible(self, request, view, action):
        """订单是否在生产可见范围"""
        order = view.get_object()
        return getattr(order, "status", None) in self.VISIBLE_STATUSES

    def is_editable(self, request, view, action):
        """订单是否处于可编辑状态（生产中）"""
        order = view.get_object()
        return getattr(order, "status", None) in self.EDITABLE_STATUSES

    # ------------------- fields 过滤 -------------------

    @classmethod
    def scope_fields(cls, request, fields, instance):
        """
        非生产中订单: 所有字段只读
        """
        new_fields = deepcopy(fields)

        if instance and instance.status not in cls.EDITABLE_STATUSES:
            for field in new_fields.values():
                field.read_only = True

        return new_fields
