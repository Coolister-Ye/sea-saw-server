from copy import deepcopy
from rest_access_policy import AccessPolicy


class OrderAccessPolicyForSales(AccessPolicy):
    """
    Access policy for SALE role on Order model.

    Rules:
    - CREATE / LIST / OPTIONS / HEAD: SALE only
    - RETRIEVE / DESTROY: SALE only for own orders (or parent user's orders)
    - UPDATE / PARTIAL_UPDATE:
        SALE only for own orders & order.status == DRAFT
    """

    statements = [
        # CREATE / LIST / OPTIONS / HEAD — only sales
        {
            "action": ["create", "list", "<method:options>", "<method:head>"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "is_sales",
        },
        # RETRIEVE / DESTROY — own or subordinate orders
        {
            "action": ["retrieve", "destroy"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "is_sales and (is_owner or is_parent_of_owner)",
        },
        # UPDATE / PARTIAL_UPDATE — own order & draft
        {
            "action": ["update", "partial_update"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "is_sales and is_owner and is_draft",
        },
    ]

    # ------------------- 条件方法 -------------------

    def is_sales(self, request, view, action):
        """User is SALE"""
        return getattr(request.user.role, "role_type", None) == "SALE"

    def is_owner(self, request, view, action):
        """Record belongs to current user"""
        order = view.get_object()
        return getattr(order, "owner", None) == request.user

    def is_parent_of_owner(self, request, view, action):
        """User is in the owner's parent users"""
        order = view.get_object()
        owner = getattr(order, "owner", None)

        get_parents = getattr(owner, "get_all_parent_users", None)
        if callable(get_parents):
            return request.user in get_parents()
        return False

    def is_draft(self, request, view, action):
        """Order.status == DRAFT"""
        order = view.get_object()
        return getattr(order, "status", None) == "DRAFT"

    # ------------------- queryset 过滤 -------------------

    @classmethod
    def scope_queryset(cls, request, qs):
        """Sales can only see orders from visible users"""
        user = request.user

        get_visibles = getattr(user, "get_all_visible_users", None)
        if callable(get_visibles):
            visible_users = get_visibles()
        else:
            visible_users = [user]

        return qs.filter(owner__in=visible_users)

    # ------------------- fields 过滤（字段权限） -------------------

    @classmethod
    def scope_fields(cls, request, fields, instance):
        """
        Non-draft orders: fields are read-only except "payments" (modifiable).
        """
        new_fields = deepcopy(fields)

        if instance and getattr(instance, "status", None) != "DRAFT":
            editable = {"payments"}  # whitelist

            for name, field in new_fields.items():
                if name not in editable:
                    field.read_only = True

        return new_fields
