import uuid
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .base import BaseModel
from .contact import Contact


class ContractStageType(models.TextChoices):
    """Contract Stage Enum"""

    IN_PROGRESS = "in_progress", _("In Progress")
    FINISHED = "finished", _("Finished")
    CANCELLED = "cancelled", _("Cancelled")
    DELAYED = "delayed", _("Delayed")
    ISSUE_REPORTED = "issue_reported", _("Issue Reported")


class Contract(BaseModel):
    """
    Contract Model:
    - Supports contract meta info
    - Linked with Contact
    - Uses soft delete inherited from BaseModel
    """

    contract_code = models.CharField(
        max_length=100,
        unique=True,
        null=False,
        blank=False,
        verbose_name=_("Contract Code"),
        help_text=_("Unique identifier for the contract."),
    )

    stage = models.CharField(
        max_length=32,
        choices=ContractStageType.choices,
        default=ContractStageType.IN_PROGRESS,
        verbose_name=_("Stage"),
    )

    contract_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Contract Date"),
    )

    contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contracts",
        verbose_name=_("Contact"),
    )

    class Meta:
        verbose_name = _("Contract")
        verbose_name_plural = _("Contracts")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.contract_code}"

    def generate_code(self):
        year = timezone.now().year
        return f"CT-{year}-{uuid.uuid4().hex[:8].upper()}"

    def save(self, *args, **kwargs):
        # auto-generate only if empty
        if not self.contract_code:
            self.contract_code = self.generate_code()

        super().save(*args, **kwargs)
