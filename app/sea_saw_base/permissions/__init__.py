"""
通用权限类

这个模块包含可在多个 app 中复用的通用权限类。
"""

from .django_model_permission import CustomDjangoModelPermission
from .field_permission import FieldPermission
from .role_permission import (
    IsAdmin,
    IsSale,
    IsProduction,
    IsWarehouse,
    IsPurchase,
)

__all__ = [
    "CustomDjangoModelPermission",
    "FieldPermission",
    "IsAdmin",
    "IsSale",
    "IsProduction",
    "IsWarehouse",
    "IsPurchase",
]
