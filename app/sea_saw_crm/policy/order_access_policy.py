from copy import deepcopy
from rest_access_policy import AccessPolicy


class OrderAccessPolicy(AccessPolicy):
    """
    Unified access policy for Order model.
    Roles:
    - ADMIN
    - SALE
    - PRODUCTION
    - WAREHOUSE
    """

    statements = [
        # ================= ADMIN =================
        {
            "action": ["*"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "is_admin",
        },
        # ================= SALE =================
        {
            "action": ["create", "list", "<method:options>", "<method:head>"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "is_sales",
        },
        {
            "action": ["retrieve", "destroy"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "sales_can_retrieve_or_destroy",
        },
        {
            "action": ["update", "partial_update"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "sales_can_edit",
        },
        # ================= PRODUCTION =================
        {
            "action": ["list", "<method:options>", "<method:head>"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "is_production",
        },
        {
            "action": ["retrieve"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "production_can_view_object",
        },
        {
            "action": ["update", "partial_update"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "production_can_edit_object",
        },
        # ================= WAREHOUSE =================
        {
            "action": ["list", "<method:options>", "<method:head>"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "is_warehouse",
        },
        {
            "action": ["retrieve"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "warehouse_can_view_object",
        },
        {
            "action": ["update", "partial_update"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "warehouse_can_edit_object",
        },
    ]

    # =====================================================
    # Role checks
    # =====================================================

    def _role(self, request):
        return getattr(request.user.role, "role_type", None)

    def is_admin(self, request, view, action):
        return self._role(request) == "ADMIN"

    def is_sales(self, request, view, action):
        return self._role(request) == "SALE"

    def is_production(self, request, view, action):
        return self._role(request) == "PRODUCTION"

    def is_warehouse(self, request, view, action):
        return self._role(request) == "WAREHOUSE"

    # =====================================================
    # SALE object-level
    # =====================================================

    def sales_can_retrieve_or_destroy(self, request, view, action):
        if not self.is_sales(request, view, action):
            return False

        order = view.get_object()
        owner = getattr(order, "owner", None)

        if owner == request.user:
            return True

        get_parents = getattr(owner, "get_all_parent_users", None)
        return callable(get_parents) and request.user in get_parents()

    def sales_can_edit(self, request, view, action):
        if not self.is_sales(request, view, action):
            return False

        order = view.get_object()
        return order.owner == request.user and order.status == "DRAFT"

    # =====================================================
    # PRODUCTION object-level
    # =====================================================

    PRODUCTION_VISIBLE_STATUSES = {
        "ORDER_CONFIRMED",
        "IN_PRODUCTION",
        "PRODUCTION_COMPLETED",
        "IN_OUTBOUND",
        "OUTBOUND_COMPLETED",
        "COMPLETED",
        "CANCELLED",
        "ISSUE_REPORTED",
    }

    PRODUCTION_EDITABLE_STATUSES = {
        "ORDER_CONFIRMED",
        "IN_PRODUCTION",
    }

    def production_can_view_object(self, request, view, action):
        if not self.is_production(request, view, action):
            return False
        return view.get_object().status in self.PRODUCTION_VISIBLE_STATUSES

    def production_can_edit_object(self, request, view, action):
        if not self.is_production(request, view, action):
            return False
        return view.get_object().status in self.PRODUCTION_EDITABLE_STATUSES

    # =====================================================
    # WAREHOUSE object-level
    # =====================================================

    WAREHOUSE_VISIBLE_STATUSES = {
        "PRODUCTION_COMPLETED",
        "IN_OUTBOUND",
        "OUTBOUND_COMPLETED",
        "COMPLETED",
        "CANCELLED",
        "ISSUE_REPORTED",
    }

    WAREHOUSE_EDITABLE_STATUSES = {
        "PRODUCTION_COMPLETED",
        "IN_OUTBOUND",
    }

    def warehouse_can_view_object(self, request, view, action):
        if not self.is_warehouse(request, view, action):
            return False
        return view.get_object().status in self.WAREHOUSE_VISIBLE_STATUSES

    def warehouse_can_edit_object(self, request, view, action):
        if not self.is_warehouse(request, view, action):
            return False
        return view.get_object().status in self.WAREHOUSE_EDITABLE_STATUSES

    # =====================================================
    # queryset scope (list 可见性)
    # =====================================================

    @classmethod
    def scope_queryset(cls, request, qs):
        role = getattr(request.user.role, "role_type", None)

        if role == "SALE":
            user = request.user
            get_visibles = getattr(user, "get_all_visible_users", None)
            visible_users = get_visibles() if callable(get_visibles) else [user]
            return qs.filter(owner__in=visible_users)

        if role == "PRODUCTION":
            return qs.filter(status__in=cls.PRODUCTION_VISIBLE_STATUSES)

        if role == "WAREHOUSE":
            return qs.filter(status__in=cls.WAREHOUSE_VISIBLE_STATUSES)

        return qs

    # =====================================================
    # field-level permissions
    # =====================================================

    @classmethod
    def scope_fields(cls, request, fields, instance):
        role = getattr(request.user.role, "role_type", None)
        new_fields = deepcopy(fields)

        if not instance or role == "ADMIN":
            return new_fields

        status = instance.status

        if role == "SALE" and status != "DRAFT":
            for name, field in new_fields.items():
                if name != "payments":
                    field.read_only = True

        if role == "PRODUCTION" and status not in cls.PRODUCTION_EDITABLE_STATUSES:
            for field in new_fields.values():
                field.read_only = True

        if role == "WAREHOUSE" and status not in cls.WAREHOUSE_EDITABLE_STATUSES:
            for field in new_fields.values():
                field.read_only = True

        return new_fields
