"""
Order-related enumerations
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class UnitType(models.TextChoices):
    """Unit Enum"""

    KGS = "kgs", _("KGS")
    LBS = "lbs", _("LBS")


class CurrencyType(models.TextChoices):
    """Currency Enum"""

    USD = "USD", _("USD")
    EUR = "EUR", _("EUR")
    GBP = "GBP", _("GBP")
    CNY = "CNY", _("CNY")
    HKD = "HKD", _("HKD")
    JPY = "JPY", _("JPY")


class ShipmentTermType(models.TextChoices):
    """Shipment Term Enum"""

    SEA = "sea", _("Sea")
    AIR = "air", _("Air")
    RAIL = "rail", _("Rail")
    ROAD = "road", _("Road")
    MULTIMODAL = "multimodal", _("Multimodal")


class IncoTermsType(models.TextChoices):
    """Incoterms (International Commercial Terms) Enum"""

    # Any Mode of Transport
    EXW = "EXW", _("EXW - Ex Works")
    FCA = "FCA", _("FCA - Free Carrier")
    CPT = "CPT", _("CPT - Carriage Paid To")
    CIP = "CIP", _("CIP - Carriage and Insurance Paid To")
    DAP = "DAP", _("DAP - Delivered at Place")
    DPU = "DPU", _("DPU - Delivered at Place Unloaded")
    DDP = "DDP", _("DDP - Delivered Duty Paid")

    # Sea and Inland Waterway Transport Only
    FAS = "FAS", _("FAS - Free Alongside Ship")
    FOB = "FOB", _("FOB - Free on Board")
    CFR = "CFR", _("CFR - Cost and Freight")
    CIF = "CIF", _("CIF - Cost, Insurance and Freight")
