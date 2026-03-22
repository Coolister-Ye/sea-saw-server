from django.db import models
from django.utils.translation import gettext_lazy as _
from sea_saw_base.models import BaseModel, CurrencyType


class BankAccount(BaseModel):
    """
    Bank account information for an Account (customer/supplier).
    An Account can have multiple bank accounts.
    """

    account = models.ForeignKey(
        "Account",
        on_delete=models.CASCADE,
        related_name="bank_accounts",
        null=True,
        blank=True,
        verbose_name=_("Account"),
        help_text=_("The account (company) this bank account belongs to."),
    )

    bank_name = models.CharField(
        max_length=255,
        verbose_name=_("Bank Name"),
        help_text=_("Name of the bank."),
    )

    account_number = models.CharField(
        max_length=255,
        verbose_name=_("Account Number"),
        help_text=_("Bank account number."),
    )

    account_holder = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Account Holder"),
        help_text=_("Name of the account holder."),
    )

    currency = models.CharField(
        max_length=10,
        choices=CurrencyType.choices,
        default=CurrencyType.USD,
        verbose_name=_("Currency"),
        help_text=_("Currency of the bank account."),
    )

    swift_code = models.CharField(
        max_length=11,
        null=True,
        blank=True,
        verbose_name=_("SWIFT / BIC Code"),
        help_text=_("International bank identifier code (8 or 11 characters)."),
    )

    branch = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Branch"),
        help_text=_("Branch name of the bank."),
    )

    bank_address = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Bank Address"),
        help_text=_("Address of the bank or branch."),
    )

    is_primary = models.BooleanField(
        default=False,
        verbose_name=_("Primary Account"),
        help_text=_("Mark as the primary bank account for this account."),
    )

    remark = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Remark"),
        help_text=_("Additional notes about this bank account."),
    )

    class Meta:
        verbose_name = _("Bank Account")
        verbose_name_plural = _("Bank Accounts")
        ordering = ["-is_primary", "bank_name"]

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"
