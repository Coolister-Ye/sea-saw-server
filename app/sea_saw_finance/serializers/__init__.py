"""
Payment Serializers Package

Provides serializers for unified Payment model with GenericForeignKey support.
"""

from .payment_nested import (
    PaymentNestedSerializer,
    PaymentNestedSerializerForAdmin,
    PaymentNestedSerializerForSales,
    PaymentNestedSerializerForProduction,
    PaymentNestedSerializerForWarehouse,
)
from .payment_standalone import (
    PaymentStandaloneSerializer,
    PaymentStandaloneSerializerForAdmin,
    PaymentStandaloneSerializerForSales,
    PaymentStandaloneSerializerForProduction,
    PaymentStandaloneSerializerForWarehouse,
)

# Legacy alias for backward compatibility
PaymentRecordSerializer = PaymentNestedSerializer

__all__ = [
    # Nested variants
    "PaymentNestedSerializer",
    "PaymentNestedSerializerForAdmin",
    "PaymentNestedSerializerForSales",
    "PaymentNestedSerializerForProduction",
    "PaymentNestedSerializerForWarehouse",
    # Standalone variants
    "PaymentStandaloneSerializer",
    "PaymentStandaloneSerializerForAdmin",
    "PaymentStandaloneSerializerForSales",
    "PaymentStandaloneSerializerForProduction",
    "PaymentStandaloneSerializerForWarehouse",
    # Legacy aliases
    "PaymentRecordSerializer",
]
