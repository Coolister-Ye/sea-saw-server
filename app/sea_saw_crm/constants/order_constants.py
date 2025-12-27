from ..models import OrderStatusType


class OrderStatus:
    """Order status groups for permission & visibility"""

    PRODUCTION_VISIBLE = {
        OrderStatusType.ORDER_CONFIRMED,
        OrderStatusType.IN_PRODUCTION,
        OrderStatusType.PRODUCTION_COMPLETED,
        OrderStatusType.IN_OUTBOUND,
        OrderStatusType.OUTBOUND_COMPLETED,
        OrderStatusType.COMPLETED,
        OrderStatusType.CANCELLED,
        OrderStatusType.ISSUE_REPORTED,
    }

    PRODUCTION_EDITABLE = {
        OrderStatusType.ORDER_CONFIRMED,
        OrderStatusType.IN_PRODUCTION,
    }

    WAREHOUSE_VISIBLE = {
        OrderStatusType.PRODUCTION_COMPLETED,
        OrderStatusType.IN_OUTBOUND,
        OrderStatusType.OUTBOUND_COMPLETED,
        OrderStatusType.COMPLETED,
        OrderStatusType.CANCELLED,
        OrderStatusType.ISSUE_REPORTED,
    }

    WAREHOUSE_EDITABLE = {
        OrderStatusType.PRODUCTION_COMPLETED,
        OrderStatusType.IN_OUTBOUND,
    }
