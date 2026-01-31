"""
Secure Attachment Download View with Permission Checks
安全的附件下载视图，带权限检查
"""
import os
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response

from ..models import Attachment


class SecureAttachmentDownloadView(APIView):
    """
    Secure file download view with permission checks.

    Security features:
    1. User must be authenticated
    2. User must have access to the related entity (Order, ProductionOrder, etc.)
    3. File path is validated to prevent directory traversal attacks
    4. Uses X-Accel-Redirect (Nginx) for efficient file serving in production

    URL Pattern: /api/sea-saw-crm/attachments/<attachment_id>/download/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, attachment_id):
        """
        Download attachment file with permission check.

        Args:
            attachment_id: ID of the attachment

        Returns:
            FileResponse with the file content (development)
            Response with X-Accel-Redirect header (production with Nginx)
        """
        try:
            # Get attachment instance
            attachment = Attachment.objects.get(pk=attachment_id)
        except Attachment.DoesNotExist:
            raise Http404("Attachment not found")

        # Check permissions on related entity
        if not self._has_permission(request.user, attachment):
            return HttpResponseForbidden(
                "You do not have permission to access this attachment."
            )

        # Get file path
        file_path = attachment.file.path

        # Validate file exists
        if not os.path.exists(file_path):
            raise Http404("File not found")

        # Security: prevent directory traversal
        media_root = str(settings.MEDIA_ROOT)
        file_abs_path = os.path.abspath(file_path)
        if not file_abs_path.startswith(os.path.abspath(media_root)):
            return HttpResponseForbidden("Invalid file path")

        # Use X-Accel-Redirect in production (Nginx)
        if not settings.DEBUG:
            # Convert absolute path to relative path for Nginx
            # Nginx location: /protected-media/ -> MEDIA_ROOT
            relative_path = os.path.relpath(file_abs_path, media_root)
            protected_url = f"/protected-media/{relative_path}"

            response = Response(status=status.HTTP_200_OK)
            response['X-Accel-Redirect'] = protected_url
            response['Content-Type'] = self._get_content_type(attachment.file_name)
            response['Content-Disposition'] = f'attachment; filename="{attachment.file_name}"'
            return response

        # Development: serve file directly with Django
        response = FileResponse(
            open(file_path, 'rb'),
            content_type=self._get_content_type(attachment.file_name)
        )
        response['Content-Disposition'] = f'attachment; filename="{attachment.file_name}"'
        return response

    def _has_permission(self, user, attachment):
        """
        Check if user has permission to access the attachment's related entity.

        Permission Logic (multi-level security):
        1. Superusers and staff can access all attachments
        2. Users can access attachments if they:
           - Own the related entity (owner field)
           - Created the related entity (created_by field)
           - Updated the related entity (updated_by field)
           - Have visibility to the entity owner based on role hierarchy

        Args:
            user: The requesting user
            attachment: The Attachment instance

        Returns:
            bool: True if user has permission, False otherwise
        """
        # Get the related entity
        related_object = attachment.related_object

        if not related_object:
            # Orphaned attachment - deny access
            return False

        # Superusers and staff have full access
        if user.is_superuser or user.is_staff:
            return True

        # Check if user is the owner of the related entity
        if hasattr(related_object, 'owner') and related_object.owner == user:
            return True

        # Check if user created the related entity
        if hasattr(related_object, 'created_by') and related_object.created_by == user:
            return True

        # Check if user updated the related entity (has edit access)
        if hasattr(related_object, 'updated_by') and related_object.updated_by == user:
            return True

        # Role-based access: check if user can see the entity owner
        # based on role hierarchy (using the existing get_all_visible_users method)
        if hasattr(related_object, 'owner') and related_object.owner:
            visible_users = user.get_all_visible_users()
            if related_object.owner in visible_users:
                return True

        # Same department access (optional - uncomment if needed)
        # if hasattr(related_object, 'owner') and related_object.owner:
        #     if user.department and user.department == related_object.owner.department:
        #         return True

        # Default: deny access
        return False

    def _get_content_type(self, filename):
        """
        Determine content type from file extension.

        Args:
            filename: Name of the file

        Returns:
            str: MIME type
        """
        import mimetypes
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or 'application/octet-stream'
