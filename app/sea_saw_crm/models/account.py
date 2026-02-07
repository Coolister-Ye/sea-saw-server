from django.db import models
from django.utils.translation import gettext_lazy as _
from sea_saw_base.models import BaseModel


class Account(BaseModel):
    """
    Unified Account model - Salesforce style.
    Represents an organization entity (company/business).

    Roles (Customer/Supplier) are implicitly defined through business relationships:
    - Has Order associations → Customer
    - Has PurchaseOrder associations → Supplier
    - Has both → Both Customer and Supplier
    """

    account_name = models.CharField(
        max_length=255,
        verbose_name=_("Account Name"),
        help_text=_("The name of the account (company/organization)."),
    )

    email = models.EmailField(
        null=True,
        blank=True,
        verbose_name=_("Email Address"),
        help_text=_("Contact email of the account."),
    )

    mobile = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Mobile Number"),
        help_text=_("The mobile phone number of the account."),
    )

    phone = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Phone Number"),
        help_text=_("The landline phone number of the account."),
    )

    address = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Address"),
        help_text=_("The address of the account."),
    )

    # Optional extended fields
    website = models.URLField(
        null=True,
        blank=True,
        verbose_name=_("Website"),
        help_text=_("The website URL of the account."),
    )

    industry = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Industry"),
        help_text=_("The industry sector of the account."),
    )

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Additional notes or description about the account."),
    )

    class Meta:
        verbose_name = _("Account")
        verbose_name_plural = _("Accounts")
        ordering = ["account_name"]

    def __str__(self):
        return self.account_name or _("Unnamed Account")

    @property
    def is_customer(self) -> bool:
        """
        Returns True if this account has any sales orders associated.
        An account is considered a customer if it has Order relationships.
        """
        if hasattr(self, "orders"):
            return self.orders.exists()
        return False

    @property
    def is_supplier(self) -> bool:
        """
        Returns True if this account has any purchase orders associated.
        An account is considered a supplier if it has PurchaseOrder relationships.
        """
        if hasattr(self, "purchase_orders"):
            return self.purchase_orders.exists()
        return False

    @property
    def roles(self) -> list:
        """
        Returns a list of roles based on business relationships.
        - CUSTOMER: Has sales orders
        - SUPPLIER: Has purchase orders
        - PROSPECT: No business relationships yet
        """
        result = []
        if self.is_customer:
            result.append("CUSTOMER")
        if self.is_supplier:
            result.append("SUPPLIER")
        return result or ["PROSPECT"]
