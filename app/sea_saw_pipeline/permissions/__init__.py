"""
Pipeline Permissions
"""

from .pipeline_permission import (
    PipelineAdminPermission,
    PipelineSalePermission,
    PipelineProductionPermission,
    PipelineWarehousePermission,
    PipelinePurchasePermission,
)
from .pipeline_transition_permission import CanTransitionPipeline

# Aliases for default permissions
PipelinePermission = PipelineAdminPermission
PipelineTransitionPermission = CanTransitionPipeline

__all__ = [
    "PipelinePermission",
    "PipelineAdminPermission",
    "PipelineSalePermission",
    "PipelineProductionPermission",
    "PipelineWarehousePermission",
    "PipelinePurchasePermission",
    "PipelineTransitionPermission",
    "CanTransitionPipeline",
]
