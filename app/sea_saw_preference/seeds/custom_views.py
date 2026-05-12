"""
System view seed data.

Each entry will be created via get_or_create on app startup (post_migrate).
Existing records are never overwritten — edit them directly in the admin panel.

params convention for date-relative filters:
  Use plain Django ORM lookup keys. If a value needs to be resolved to
  "today" at query time, store it as the string "__today__" and resolve
  it on the frontend (resolveParams).
"""

SYSTEM_VIEWS = [
    {
        "entity": "order",
        "key": "all",
        "name": "All",
        "params": {},
    },
    {
        "entity": "order",
        "key": "pending",
        "name": "待发货",
        "params": {
            "status": "confirmed",
            "etd__gte": "__today__",
        },
    },
    {
        "entity": "order",
        "key": "overdue",
        "name": "逾期未发",
        "params": {
            "status": "confirmed",
            "etd__lt": "__today__",
        },
    },
]


def seed_custom_views(sender, **kwargs):  # noqa: ARG001
    """Idempotent seed — safe to run multiple times."""
    from sea_saw_preference.models import CustomView

    for view in SYSTEM_VIEWS:
        CustomView.objects.get_or_create(
            entity=view["entity"],
            key=view["key"],
            is_system=True,
            defaults={
                "owner": None,
                "name": view["name"],
                "params": view["params"],
                "column_order": [],
                "visibility": CustomView.VisibilityChoice.PUBLIC,
                "is_default": False,
            },
        )
