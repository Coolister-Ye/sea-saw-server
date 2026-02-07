"""
Payment Admin Package
"""

from .payment import PaymentAdmin, PaymentRecordAdmin

__all__ = [
    "PaymentAdmin",
    # Legacy alias
    "PaymentRecordAdmin",
]
