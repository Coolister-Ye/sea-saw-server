"""
System filter preset seed data.

Each entry will be created via get_or_create on app startup (post_migrate).
Existing records are never overwritten — edit them directly in the admin panel.

params convention for date-relative filters:
  Use plain Django ORM lookup keys. If a value needs to be resolved to
  "today" at query time, store it as the string "__today__" and resolve
  it on the frontend (resolveParams) or via a custom DRF filter backend.
"""

SYSTEM_FILTER_PRESETS = [
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


def seed_system_filter_presets(sender, **kwargs):
    """Idempotent seed — safe to run multiple times."""
    # Import here to avoid AppRegistryNotReady errors
    from sea_saw_preference.models import UserFilterPreset

    for preset in SYSTEM_FILTER_PRESETS:
        UserFilterPreset.objects.get_or_create(
            entity=preset["entity"],
            key=preset["key"],
            preset_type=UserFilterPreset.PRESET_TYPE_SYSTEM,
            defaults={
                "name": preset["name"],
                "params": preset["params"],
                "user": None,
            },
        )
