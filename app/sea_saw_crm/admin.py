from django.contrib import admin
from safedelete.admin import SafeDeleteAdmin, highlight_deleted

from .models import Contact, Company, Field, Contract, Order, OrderProduct


# Field Admin
@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ("field_name", "field_type", "is_active", "content_type")
    search_fields = ("field_name", "field_type")
    list_filter = ("field_type", "is_active", "content_type")
    ordering = ("field_name",)  # Optional: sort fields alphabetically


# Contact Admin
@admin.register(Contact)
class ContactAdmin(SafeDeleteAdmin):
    list_display = (
        highlight_deleted,
        "first_name",
        "last_name",
        "email",
        "mobile",
        "company__company_name",
    ) + SafeDeleteAdmin.list_display
    search_fields = ("first_name", "last_name", "email", "company__company_name")
    list_filter = ("created_at", "updated_at", "company")
    ordering = ("last_name", "first_name")  # Sorting by last name and first name


# Company Admin
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("company_name", "email", "mobile", "phone", "created_at")
    search_fields = ("company_name", "email", "mobile", "phone")
    list_filter = ("created_at", "updated_at")
    ordering = ("company_name",)


@admin.register(Contract)
class ContractAdmin(SafeDeleteAdmin):
    list_display = (
        highlight_deleted,
        "id",
        "contract_code",
        "contract_date",
        "owner",
    ) + SafeDeleteAdmin.list_display
    ordering = ("created_at",)
    field_to_highlight = "id"


@admin.register(Order)
class OrderAdmin(SafeDeleteAdmin):
    list_display = (
        highlight_deleted,
        "id",
        "order_code",
        "destination_port",
        "etd",
        "deliver_date",
        "deposit",
        "deposit_date",
        "balance",
        "balance_date",
    ) + SafeDeleteAdmin.list_display
    ordering = ("created_at",)
    field_to_highlight = "id"


@admin.register(OrderProduct)
class OrderProductAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "product_name",
        "size",
        "packaging",
        "interior_packaging",
        "weight",
        "glazing",
        "net_weight",
        "quantity",
        "total_net_weight",
        "progress_material",
        "progress_quantity",
        "progress_weight",
    )
    ordering = ("created_at",)
