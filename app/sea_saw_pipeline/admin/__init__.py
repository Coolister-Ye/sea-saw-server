"""
Pipeline Admin Configuration
"""

from django.contrib import admin
from ..models import Pipeline


@admin.register(Pipeline)
class PipelineAdmin(admin.ModelAdmin):
    list_display = [
        "pipeline_code",
        "status",
        "pipeline_type",
        "account",
        "contact",
        "order_date",
        "created_at",
    ]
    list_filter = ["status", "pipeline_type", "created_at"]
    search_fields = ["pipeline_code", "company__company_name", "contact__name"]
    readonly_fields = ["created_at", "updated_at", "created_by", "updated_by"]
    date_hierarchy = "created_at"
