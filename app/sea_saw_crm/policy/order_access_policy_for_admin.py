from rest_access_policy import AccessPolicy


class OrderAccessPolicyForAdmin(AccessPolicy):
    """
    Access policy for ADMIN role on Order model.
    Admin can perform ANY action without restriction.
    """

    statements = [
        {
            "action": ["*"],  # admin may do anything
            "principal": ["authenticated"],  # must be logged in
            "effect": "allow",
            "condition": "is_admin",
        },
    ]

    # ------------------- 条件方法 -------------------

    def is_admin(self, request, view, action):
        """User is ADMIN"""
        return getattr(request.user.role, "role_type", None) == "ADMIN"
