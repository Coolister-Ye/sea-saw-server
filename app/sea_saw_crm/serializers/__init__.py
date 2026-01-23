from .company import CompanySerializer
from .contact import ContactSerializer
from .contract import ContractSerializer
from .payment import (
    PaymentStandaloneSerializer,
    PaymentNestedSerializer,
)

# Legacy alias for backward compatibility
PaymentRecordSerializer = PaymentStandaloneSerializer

from .order import (
    OrderSerializerForAdmin,
    OrderSerializerForSales,
    OrderSerializerForProduction,
    OrderSerializerForWarehouse,
    OrderItemSerializerForAdmin,
    OrderItemSerializerForSales,
    OrderItemSerializerForProduction,
    OrderItemSerializerForWarehouse,
)

from .pipeline import (
    PipelineSerializerForAdmin,
    PipelineSerializerForSales,
    PipelineSerializerForProduction,
    PipelineSerializerForWarehouse,
)

from .production import (
    ProductionItemSerializerForAdmin,
    ProductionItemSerializerForSales,
    ProductionItemSerializerForProduction,
    ProductionItemSerializerForWarehouse,
    ProductionOrderSerializerForAdmin,
    ProductionOrderSerializerForSales,
    ProductionOrderSerializerForProduction,
    ProductionOrderSerializerForWarehouse,
)

from .purchase import (
    PurchaseItemSerializer,
    PurchaseItemSerializerForAdmin,
    PurchaseItemSerializerForSales,
    PurchaseItemSerializerForProduction,
    PurchaseItemSerializerForWarehouse,
    PurchaseOrderSerializer,
    PurchaseOrderSerializerForAdmin,
    PurchaseOrderSerializerForSales,
    PurchaseOrderSerializerForProduction,
    PurchaseOrderSerializerForWarehouse,
)

from .outbound import (
    OutboundItemSerializer,
    OutboundOrderSerializerForAdmin,
    OutboundOrderSerializerForSales,
    OutboundOrderSerializerForProduction,
    OutboundOrderSerializerForWarehouse,
    OutboundItemSerializerForAdmin,
    OutboundItemSerializerForSales,
    OutboundItemSerializerForProduction,
    OutboundItemSerializerForWarehouse,
)

from .field import FieldSerializer
