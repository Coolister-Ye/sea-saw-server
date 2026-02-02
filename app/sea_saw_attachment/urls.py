"""
Sea-Saw Attachment URLs
"""
from django.urls import path
from .views import SecureAttachmentDownloadView

app_name = "sea-saw-attachment"

urlpatterns = [
    # Secure attachment download endpoint
    path(
        "<int:attachment_id>/download/",
        SecureAttachmentDownloadView.as_view(),
        name="attachment-download",
    ),
]
