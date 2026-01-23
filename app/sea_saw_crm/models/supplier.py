"""
Supplier Model
"""
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .base import BaseModel
from .company import Company


class Supplier(BaseModel):
    """
    Supplier - 供应商信息

    管理供应商的基本信息、联系方式、评级等
    """

    supplier_code = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name=_("Supplier Code"),
        help_text=_("Unique identifier for this supplier."),
    )

    name = models.CharField(
        max_length=200,
        verbose_name=_("Supplier Name"),
        help_text=_("Name of the supplier."),
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="suppliers",
        verbose_name=_("Company"),
        help_text=_("The company associated with this supplier."),
    )

    # Contact Information
    contact_person = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name=_("Contact Person"),
        help_text=_("Main contact person at supplier."),
    )

    phone = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("Phone"),
    )

    mobile = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("Mobile"),
    )

    email = models.EmailField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name=_("Email"),
    )

    fax = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("Fax"),
    )

    # Address Information
    address = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Address"),
    )

    country = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Country"),
    )

    state = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("State/Province"),
    )

    city = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("City"),
    )

    postal_code = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name=_("Postal Code"),
    )

    # Business Information
    tax_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Tax ID"),
        help_text=_("Tax identification number."),
    )

    website = models.URLField(
        null=True,
        blank=True,
        verbose_name=_("Website"),
    )

    # Payment & Terms
    payment_terms = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name=_("Payment Terms"),
        help_text=_("Standard payment terms for this supplier."),
    )

    currency = models.CharField(
        max_length=10,
        default="CNY",
        verbose_name=_("Currency"),
        help_text=_("Preferred currency for transactions."),
    )

    credit_limit = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Credit Limit"),
    )

    # Supplier Rating & Status
    rating = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Rating"),
        help_text=_("Supplier rating (1-5 stars)."),
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Active"),
        help_text=_("Whether this supplier is currently active."),
    )

    is_approved = models.BooleanField(
        default=False,
        verbose_name=_("Is Approved"),
        help_text=_("Whether this supplier has been approved."),
    )

    # Additional Information
    remark = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Remark"),
    )

    class Meta:
        verbose_name = _("Supplier")
        verbose_name_plural = _("Suppliers")
        ordering = ["name"]
        indexes = [
            models.Index(fields=["supplier_code"]),
            models.Index(fields=["name"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name or self.supplier_code or _("Unnamed Supplier")

    def generate_code(self):
        """Auto-generate supplier code"""
        year = timezone.now().year
        count = Supplier.objects.filter(created_at__year=year).count() + 1
        return f"SUP{year}-{count:06d}"

    def save(self, *args, **kwargs):
        """Auto-generate supplier code if not set"""
        if not self.supplier_code:
            self.supplier_code = self.generate_code()
        super().save(*args, **kwargs)
