"""
File Upload Validators - Security validation for file uploads
文件上传验证器 - 文件上传的安全验证
"""
import mimetypes
import logging
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.files.uploadedfile import UploadedFile

# Try to import python-magic for advanced MIME type detection
# Falls back to mimetypes if not available (development environments)
try:
    import magic

    HAS_MAGIC = True
except (ImportError, OSError):
    HAS_MAGIC = False
    logging.warning(
        "python-magic not available. File upload validation will use basic mimetypes. "
        "For production, install libmagic: brew install libmagic (macOS) or apt-get install libmagic1 (Linux)"
    )

logger = logging.getLogger(__name__)


# Security: Whitelist of allowed MIME types
# 安全：允许的MIME类型白名单
ALLOWED_MIME_TYPES = {
    # Documents
    "application/pdf": [".pdf"],
    "application/msword": [".doc"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [
        ".docx"
    ],
    "application/vnd.ms-excel": [".xls"],
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    "application/vnd.ms-powerpoint": [".ppt"],
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": [
        ".pptx"
    ],
    "text/plain": [".txt"],
    "text/csv": [".csv"],
    # Images
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"],
    "image/gif": [".gif"],
    "image/bmp": [".bmp"],
    "image/webp": [".webp"],
    "image/svg+xml": [".svg"],
    # Archives (for batch documents)
    "application/zip": [".zip"],
    "application/x-rar-compressed": [".rar"],
    "application/x-7z-compressed": [".7z"],
    "application/gzip": [".gz"],
    "application/x-tar": [".tar"],
    # Other common formats
    "application/json": [".json"],
    "application/xml": [".xml"],
    "text/xml": [".xml"],
}

# Maximum file size: 50MB (adjust based on your needs)
# 最大文件大小：50MB（根据需要调整）
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes

# Dangerous file extensions that should never be uploaded
# 危险的文件扩展名，永远不应该上传
DANGEROUS_EXTENSIONS = {
    ".exe",
    ".dll",
    ".bat",
    ".cmd",
    ".sh",
    ".ps1",
    ".psm1",
    ".msi",
    ".app",
    ".deb",
    ".rpm",
    ".dmg",
    ".pkg",
    ".scr",
    ".com",
    ".pif",
    ".application",
    ".gadget",
    ".msp",
    ".jar",
    ".js",
    ".jse",
    ".vbs",
    ".vbe",
    ".ws",
    ".wsf",
    ".wsh",
    ".hta",
    ".cpl",
    ".msc",
    ".reg",
    ".scf",
    ".lnk",
    ".inf",
    ".vb",
}


def validate_file_extension(value):
    """
    Validate file extension against dangerous extensions.

    Args:
        value: UploadedFile instance

    Raises:
        ValidationError: If file extension is dangerous
    """
    import os

    if not isinstance(value, UploadedFile):
        return

    ext = os.path.splitext(value.name)[1].lower()

    if ext in DANGEROUS_EXTENSIONS:
        raise ValidationError(
            _('File extension "%(ext)s" is not allowed for security reasons.'),
            params={"ext": ext},
            code="dangerous_extension",
        )


def validate_file_size(value):
    """
    Validate file size.

    Args:
        value: UploadedFile instance

    Raises:
        ValidationError: If file size exceeds maximum
    """
    if not isinstance(value, UploadedFile):
        return

    if value.size > MAX_FILE_SIZE:
        size_mb = value.size / (1024 * 1024)
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        raise ValidationError(
            _("File size %(size).2fMB exceeds maximum allowed size of %(max)dMB."),
            params={"size": size_mb, "max": max_mb},
            code="file_too_large",
        )


def validate_file_mime_type(value):
    """
    Validate file MIME type using python-magic for security.

    This checks the actual file content, not just the extension,
    preventing users from uploading malicious files with fake extensions.

    Falls back to mimetypes if python-magic is not available.

    Args:
        value: UploadedFile instance

    Raises:
        ValidationError: If MIME type is not allowed
    """
    if not isinstance(value, UploadedFile):
        return

    import os

    # Get file extension
    ext = os.path.splitext(value.name)[1].lower()

    # Method 1: Check declared content_type (from browser)
    declared_type = value.content_type

    # Method 2: Detect actual MIME type from file content (more secure)
    if HAS_MAGIC:
        # Use python-magic for content-based detection (production)
        try:
            # Read first 2048 bytes to detect MIME type
            value.seek(0)
            file_head = value.read(2048)
            value.seek(0)  # Reset file pointer

            # Use python-magic to detect actual MIME type
            detected_type = magic.from_buffer(file_head, mime=True)
            logger.debug(f"Detected MIME type using magic: {detected_type}")
        except Exception as e:
            logger.warning(f"Magic detection failed: {e}, falling back to mimetypes")
            # Fallback to mimetypes if python-magic fails
            detected_type, _ = mimetypes.guess_type(value.name)
            if not detected_type:
                detected_type = declared_type
    else:
        # Fallback to mimetypes (development environment)
        logger.debug("Using mimetypes for MIME detection (magic not available)")
        detected_type, _ = mimetypes.guess_type(value.name)
        if not detected_type:
            detected_type = declared_type
            logger.warning(
                f"Could not detect MIME type, using declared type: {declared_type}"
            )

    # Validate against whitelist
    if detected_type not in ALLOWED_MIME_TYPES:
        raise ValidationError(
            _('File type "%(type)s" is not allowed. Allowed types: %(allowed)s'),
            params={"type": detected_type, "allowed": ", ".join(ALLOWED_MIME_TYPES.keys())},
            code="invalid_mime_type",
        )

    # Validate extension matches MIME type
    allowed_extensions = ALLOWED_MIME_TYPES[detected_type]
    if ext not in allowed_extensions:
        raise ValidationError(
            _(
                'File extension "%(ext)s" does not match detected file type "%(type)s". '
                "Expected extensions: %(expected)s"
            ),
            params={
                "ext": ext,
                "type": detected_type,
                "expected": ", ".join(allowed_extensions),
            },
            code="extension_mismatch",
        )


def validate_file_upload(value):
    """
    Combined validator for file uploads.
    Runs all security checks in sequence.

    Args:
        value: UploadedFile instance

    Raises:
        ValidationError: If any validation fails
    """
    if not value:
        return

    # Run all validators
    validate_file_extension(value)
    validate_file_size(value)
    validate_file_mime_type(value)
