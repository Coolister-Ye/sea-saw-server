from .django_model_permission import CustomDjangoModelPermission
from .field_permission import FieldPermission
from .pipeline_transition_permission import CanTransitionPipeline
from .payment_permission import CanManagePayment

# 通用角色权限类
from .role_permission import IsAdmin, IsSale, IsProduction, IsWarehouse, IsPurchase

# Company 特定权限类
from .company_permission import CompanyAdminPermission, CompanySalePermission

# Contact 特定权限类
from .contact_permission import ContactAdminPermission, ContactSalePermission

# Order 特定权限类
from .order_permission import OrderAdminPermission, OrderSalePermission

# Pipeline 特定权限类
from .pipeline_permission import (
    PipelineAdminPermission,
    PipelineSalePermission,
    PipelineProductionPermission,
    PipelineWarehousePermission,
    PipelinePurchasePermission,
)

__all__ = [
    "CustomDjangoModelPermission",
    "FieldPermission",
    "CanTransitionPipeline",
    "CanManagePayment",
    # 通用角色权限
    "IsAdmin",
    "IsSale",
    "IsProduction",
    "IsWarehouse",
    "IsPurchase",
    # Company 权限
    "CompanyAdminPermission",
    "CompanySalePermission",
    # Contact 权限
    "ContactAdminPermission",
    "ContactSalePermission",
    # Order 权限
    "OrderAdminPermission",
    "OrderSalePermission",
    # Pipeline 权限
    "PipelineAdminPermission",
    "PipelineSalePermission",
    "PipelineProductionPermission",
    "PipelineWarehousePermission",
    "PipelinePurchasePermission",
]
