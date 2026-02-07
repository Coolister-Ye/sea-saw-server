from copy import deepcopy
from rest_access_policy import AccessPolicy


class OrderAccessPolicyForWarehouse(AccessPolicy):
    """
    Access policy for WAREHOUSE role on Order model.

    Permissions:
    - LIST / RETRIEVE / OPTIONS / HEAD: allowed for WAREHOUSE when order is production completed or later
    - UPDATE / PARTIAL_UPDATE: allowed for WAREHOUSE only when order is IN_OUTBOUND
    """

    statements = [
        # 仓库可以查看已完成生产之后的订单
        {
            "action": ["list", "retrieve", "<method:options>", "<method:head>"],
            "principal": ["*"],
            "effect": "allow",
            "condition": "is_warehouse and is_production_completed",
        },
        # 仓库仅可在 IN_OUTBOUND 阶段修改
        {
            "action": ["update", "partial_update"],
            "principal": ["*"],
            "effect": "allow",
            "condition": "is_warehouse and is_in_outbound",
        },
    ]

    # ------------------- 条件方法 -------------------

    def is_warehouse(self, request, view, action):
        """判断用户是否为 WAREHOUSE"""
        return getattr(request.user.role, "role_type", None) == "WAREHOUSE"

    def is_production_completed(self, request, view, action):
        """订单是否处于生产完成或之后阶段"""
        order = view.get_object()
        status = getattr(order, "status", None)

        allowed_status = {
            "PRODUCTION_COMPLETED",
            "IN_OUTBOUND",
            "OUTBOUND_COMPLETED",
            "COMPLETED",
            "CANCELLED",
            "ISSUE_REPORTED",
        }

        return status in allowed_status

    def is_in_outbound(self, request, view, action):
        """订单是否处于可由仓库编辑的出库阶段"""
        order = view.get_object()
        status = getattr(order, "status", None)
        return status in {"PRODUCTION_COMPLETED", "IN_OUTBOUND"}

    # ------------------- fields 过滤 -------------------

    @classmethod
    def scope_fields(cls, request, fields, instance):
        """
        非 IN_OUTBOUND 阶段：所有字段只读
        """
        new_fields = deepcopy(fields)

        if instance and instance.status != "IN_OUTBOUND":
            for field in new_fields.values():
                field.read_only = True

        return new_fields
