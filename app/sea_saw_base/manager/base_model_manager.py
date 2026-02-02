from django.db import models


class BaseModelManager(models.Manager):
    """
    Base manager handling audit fields:
    - owner
    - created_by
    - updated_by

    Supports:
    - direct create/update
    - drf-writable-nested
    - serializer context injection via `_user`
    """

    def _extract_user(self, kwargs):
        """
        Extract internal user from kwargs.
        `_user` is a private convention, never stored in DB.
        """
        return kwargs.pop("_user", None)

    # ----------------------
    # CREATE
    # ----------------------
    def create(self, **kwargs):
        user = self._extract_user(kwargs)

        if user:
            kwargs.setdefault("owner", user)
            kwargs.setdefault("created_by", user)

        return super().create(**kwargs)

    def create_with_user(self, *, user=None, **kwargs):
        """
        Explicit creation API for Admin / Celery / Script
        """
        if user:
            kwargs["_user"] = user
        return self.create(**kwargs)

    # ----------------------
    # UPDATE (queryset.update)
    # ----------------------
    def update(self, **kwargs):
        user = self._extract_user(kwargs)

        if user:
            kwargs.setdefault("updated_by", user)

        return super().update(**kwargs)
