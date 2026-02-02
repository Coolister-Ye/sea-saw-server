"""
File Path Utilities for Attachments
"""
import os
import uuid
from django.utils import timezone


def attachment_file_path(instance, filename):
    """
    Generate file upload path based on related entity type.

    Format: attachments/{entity_type}/{year}/{month}/{day}/{unique_filename}
    Example: attachments/order/2024/01/15/abc123_document.pdf

    Args:
        instance: Attachment model instance
        filename: Original filename

    Returns:
        str: Upload path for the file
    """
    # Get file extension
    ext = os.path.splitext(filename)[1]

    # Generate unique filename
    unique_filename = f"{uuid.uuid4().hex[:12]}{ext}"

    # Get entity type from content_type
    entity_type = "unknown"
    if instance.content_type:
        entity_type = instance.content_type.model

    # Generate path
    now = timezone.now()
    return f"attachments/{entity_type}/{now.year}/{now.month:02d}/{now.day:02d}/{unique_filename}"
