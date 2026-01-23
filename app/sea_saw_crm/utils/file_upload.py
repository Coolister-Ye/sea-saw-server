"""
File upload path utilities

Provides functions to generate unique file paths for uploads,
preventing name conflicts by using UUID prefixes and date-based folder structure.
"""
import os
import uuid
from datetime import datetime


def get_upload_path(instance, filename, subfolder="files"):
    """
    Generate a unique upload path for files to avoid name conflicts.

    Path structure: {subfolder}/{YYYY}/{MM}/{DD}/{uuid}_{original_filename}

    Example:
        payment_attachments/2024/01/15/a3b5c7d9-e1f2-4a5b-8c9d-0e1f2a3b4c5d_invoice.pdf

    Args:
        instance: The model instance (not used, but required by Django)
        filename: Original filename
        subfolder: Base folder name (e.g., 'payment_attachments', 'production_files')

    Returns:
        str: Unique file path
    """
    # Get file extension
    ext = os.path.splitext(filename)[1].lower()

    # Get original filename without extension
    original_name = os.path.splitext(filename)[0]

    # Generate unique filename with UUID prefix
    unique_filename = f"{uuid.uuid4().hex[:12]}_{original_name}{ext}"

    # Generate date-based folder structure
    now = datetime.now()
    date_path = now.strftime("%Y/%m/%d")

    # Combine all parts
    return os.path.join(subfolder, date_path, unique_filename)


def production_file_path(instance, filename):
    """
    Upload path for production files.

    Args:
        instance: ProductionOrder model instance
        filename: Original filename

    Returns:
        str: Unique path like 'production_files/2024/01/15/abc123_file.pdf'
    """
    return get_upload_path(instance, filename, subfolder="production_files")


def payment_attachment_path(instance, filename):
    """
    Legacy upload path for payment attachments.

    Args:
        instance: PaymentRecord/OrderPayment model instance
        filename: Original filename

    Returns:
        str: Unique path like 'payment_attachments/2024/01/15/abc123_file.pdf'
    """
    return get_upload_path(instance, filename, subfolder="payment_attachments")


def order_payment_attachment_path(instance, filename):
    """
    Upload path for order payment attachments.

    Args:
        instance: OrderPayment model instance
        filename: Original filename

    Returns:
        str: Unique path like 'order_payment_attachments/2024/01/15/abc123_file.pdf'
    """
    return get_upload_path(instance, filename, subfolder="order_payment_attachments")


def purchase_payment_attachment_path(instance, filename):
    """
    Upload path for purchase payment attachments.

    Args:
        instance: PurchasePayment model instance
        filename: Original filename

    Returns:
        str: Unique path like 'purchase_payment_attachments/2024/01/15/abc123_file.pdf'
    """
    return get_upload_path(instance, filename, subfolder="purchase_payment_attachments")


def contract_file_path(instance, filename):
    """
    Upload path for contract files.

    Args:
        instance: Contract model instance
        filename: Original filename

    Returns:
        str: Unique path like 'contract_files/2024/01/15/abc123_file.pdf'
    """
    return get_upload_path(instance, filename, subfolder="contract_files")


def order_file_path(instance, filename):
    """
    Upload path for order files.

    Args:
        instance: Order model instance
        filename: Original filename

    Returns:
        str: Unique path like 'order_files/2024/01/15/abc123_file.pdf'
    """
    return get_upload_path(instance, filename, subfolder="order_files")


def outbound_file_path(instance, filename):
    """
    Upload path for outbound order files.

    Args:
        instance: OutboundOrder model instance
        filename: Original filename

    Returns:
        str: Unique path like 'outbound_files/2024/01/15/abc123_file.pdf'
    """
    return get_upload_path(instance, filename, subfolder="outbound_files")
