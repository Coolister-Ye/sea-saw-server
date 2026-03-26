"""Reusable ViewSet mixin for single and bulk XLSX export actions."""

from django.http import FileResponse
from rest_framework.exceptions import ValidationError

XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class ExportViewSetMixin:
    """Provides _export_single and _export_bulk helpers for ViewSets."""

    def _export_response(self, buf, filename) -> FileResponse:
        """Return a FileResponse streaming an xlsx BytesIO."""
        return FileResponse(
            buf,
            as_attachment=True,
            filename=filename,
            content_type=XLSX_CONTENT_TYPE,
        )

    def _export_single(self, generator_fn, get_filename_fn):
        """Handle a single-record export action.

        Args:
            generator_fn: callable(obj) -> BytesIO
            get_filename_fn: callable(obj) -> str
        """
        obj = self.get_object()
        buf = generator_fn(obj)
        return self._export_response(buf, get_filename_fn(obj))

    def _export_bulk(self, generator_fn, get_filename_fn, ids):
        """Handle a bulk export action.

        Args:
            generator_fn: callable(queryset) -> BytesIO
            get_filename_fn: callable(queryset) -> str
            ids: list of primary keys from request.data
        """
        if not ids:
            raise ValidationError({"ids": "This field is required."})
        qs = self.get_queryset().filter(pk__in=ids)
        if not qs.exists():
            raise ValidationError({"ids": "No matching records found."})
        buf = generator_fn(qs)
        return self._export_response(buf, get_filename_fn(qs))
