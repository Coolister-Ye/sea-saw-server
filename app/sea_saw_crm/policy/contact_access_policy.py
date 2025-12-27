from rest_access_policy import AccessPolicy


class ContactAccessPolicy(AccessPolicy):
    """
    Access policy for SALE role on Contact model.

    Rules:
    - CREATE / LIST / OPTIONS / HEAD: allowed for SALE or ADMIN
    - RETRIEVE: allowed for SALE only if visible, allowed for ADMIN
    - UPDATE / PARTIAL_UPDATE / DESTROY:
        allowed for SALE only for own contacts, allowed for ADMIN
    """

    statements = [
        # CREATE / LIST / OPTIONS / HEAD — only for sales & admin
        {
            "action": ["create", "list", "<method:options>", "<method:head>"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "is_sales or is_admin",
        },
        # RETRIEVE — visible contacts only
        {
            "action": ["retrieve"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "is_admin or (is_sales and is_visible)",
        },
        # UPDATE / PARTIAL_UPDATE / DESTROY — only owner or admin
        {
            "action": ["update", "partial_update", "destroy"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "is_admin or (is_sales and is_owner)",
        },
    ]

    # ------------------- 条件方法 -------------------

    def is_sales(self, request, view, action):
        """Is SALE role"""
        return getattr(request.user.role, "role_type", None) == "SALE"

    def is_admin(self, request, view, action):
        """Is ADMIN role"""
        return getattr(request.user.role, "role_type", None) == "ADMIN"

    def is_owner(self, request, view, action):
        """Record belongs to current user"""
        obj = view.get_object()
        return getattr(obj, "owner", None) == request.user

    def is_visible(self, request, view, action):
        """User can see this record"""
        obj = view.get_object()
        owner = getattr(obj, "owner", None)
        if owner is None:
            return False

        get_users = getattr(owner, "get_all_visible_users", None)
        if not callable(get_users):
            return False

        return request.user in get_users()

    # ------------------- Queryset Scope -------------------

    @classmethod
    def scope_queryset(cls, request, qs):
        """Limit LIST results: sales can only view visible contacts"""
        user = request.user

        # admin sees all
        if getattr(user.role, "role_type", None) == "ADMIN":
            return qs

        # sales: filter by visibility
        get_users = getattr(user, "get_all_visible_users", None)
        if not callable(get_users):
            return qs.none()

        return qs.filter(owner__in=get_users())
