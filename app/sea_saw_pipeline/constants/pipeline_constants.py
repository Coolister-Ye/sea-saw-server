"""
Pipeline Constants - State Machine Configuration

Defines valid state transitions and role-based permissions for Pipeline workflows.
"""

from ..models.pipeline import PipelineStatusType, PipelineType


# Pipeline 状态机配置 - 根据 pipeline_type 定义允许的状态转换
PIPELINE_STATE_MACHINE_BY_TYPE = {
    # 生产流程：Order → Production → Outbound → Completion
    PipelineType.PRODUCTION_FLOW: {
        PipelineStatusType.DRAFT: {
            PipelineStatusType.ORDER_CONFIRMED,
            PipelineStatusType.CANCELLED,
        },
        PipelineStatusType.ORDER_CONFIRMED: {
            PipelineStatusType.IN_PRODUCTION,
            PipelineStatusType.ISSUE_REPORTED,
        },
        PipelineStatusType.IN_PRODUCTION: {
            PipelineStatusType.PRODUCTION_COMPLETED,
            PipelineStatusType.ISSUE_REPORTED,
        },
        PipelineStatusType.PRODUCTION_COMPLETED: {
            PipelineStatusType.IN_OUTBOUND,
            PipelineStatusType.ISSUE_REPORTED,
        },
        PipelineStatusType.IN_OUTBOUND: {
            PipelineStatusType.OUTBOUND_COMPLETED,
            PipelineStatusType.ISSUE_REPORTED,
        },
        PipelineStatusType.OUTBOUND_COMPLETED: {
            PipelineStatusType.COMPLETED,
            PipelineStatusType.ISSUE_REPORTED,
        },
        PipelineStatusType.COMPLETED: set(),
        PipelineStatusType.CANCELLED: set(),
        PipelineStatusType.ISSUE_REPORTED: {
            PipelineStatusType.DRAFT,
            PipelineStatusType.IN_PRODUCTION,
            PipelineStatusType.IN_OUTBOUND,
            PipelineStatusType.CANCELLED,
        },
    },
    # 采购流程：Order → Purchase → Outbound → Completion
    PipelineType.PURCHASE_FLOW: {
        PipelineStatusType.DRAFT: {
            PipelineStatusType.ORDER_CONFIRMED,
            PipelineStatusType.CANCELLED,
        },
        PipelineStatusType.ORDER_CONFIRMED: {
            PipelineStatusType.IN_PURCHASE,
            PipelineStatusType.ISSUE_REPORTED,
        },
        PipelineStatusType.IN_PURCHASE: {
            PipelineStatusType.PURCHASE_COMPLETED,
            PipelineStatusType.ISSUE_REPORTED,
        },
        PipelineStatusType.PURCHASE_COMPLETED: {
            PipelineStatusType.IN_OUTBOUND,
            PipelineStatusType.ISSUE_REPORTED,
        },
        PipelineStatusType.IN_OUTBOUND: {
            PipelineStatusType.OUTBOUND_COMPLETED,
            PipelineStatusType.ISSUE_REPORTED,
        },
        PipelineStatusType.OUTBOUND_COMPLETED: {
            PipelineStatusType.COMPLETED,
            PipelineStatusType.ISSUE_REPORTED,
        },
        PipelineStatusType.COMPLETED: set(),
        PipelineStatusType.CANCELLED: set(),
        PipelineStatusType.ISSUE_REPORTED: {
            PipelineStatusType.DRAFT,
            PipelineStatusType.IN_PURCHASE,
            PipelineStatusType.IN_OUTBOUND,
            PipelineStatusType.CANCELLED,
        },
    },
    # 混合流程：Order → Production + Purchase → Outbound → Completion
    PipelineType.HYBRID_FLOW: {
        PipelineStatusType.DRAFT: {
            PipelineStatusType.ORDER_CONFIRMED,
            PipelineStatusType.CANCELLED,
        },
        PipelineStatusType.ORDER_CONFIRMED: {
            PipelineStatusType.IN_PURCHASE_AND_PRODUCTION,
            PipelineStatusType.ISSUE_REPORTED,
        },
        PipelineStatusType.IN_PURCHASE_AND_PRODUCTION: {
            PipelineStatusType.PURCHASE_AND_PRODUCTION_COMPLETED,
            PipelineStatusType.ISSUE_REPORTED,
        },
        PipelineStatusType.PURCHASE_AND_PRODUCTION_COMPLETED: {
            PipelineStatusType.IN_OUTBOUND,
            PipelineStatusType.ISSUE_REPORTED,
        },
        PipelineStatusType.IN_OUTBOUND: {
            PipelineStatusType.OUTBOUND_COMPLETED,
            PipelineStatusType.ISSUE_REPORTED,
        },
        PipelineStatusType.OUTBOUND_COMPLETED: {
            PipelineStatusType.COMPLETED,
            PipelineStatusType.ISSUE_REPORTED,
        },
        PipelineStatusType.COMPLETED: set(),
        PipelineStatusType.CANCELLED: set(),
        PipelineStatusType.ISSUE_REPORTED: {
            PipelineStatusType.DRAFT,
            PipelineStatusType.IN_PURCHASE_AND_PRODUCTION,
            PipelineStatusType.IN_OUTBOUND,
            PipelineStatusType.CANCELLED,
        },
    },
}


# 角色权限配置 - 定义每个角色可以操作的目标状态
PIPELINE_ROLE_ALLOWED_TARGET_STATES = {
    "SALE": {
        # 销售人员：管理订单确认、采购流程、取消
        PipelineStatusType.DRAFT,
        PipelineStatusType.ORDER_CONFIRMED,
        PipelineStatusType.IN_PURCHASE,
        PipelineStatusType.PURCHASE_COMPLETED,
        PipelineStatusType.CANCELLED,
    },
    "PRODUCTION": {
        # 生产人员：管理生产流程、报告问题
        PipelineStatusType.IN_PRODUCTION,
        PipelineStatusType.PRODUCTION_COMPLETED,
        PipelineStatusType.ISSUE_REPORTED,
    },
    "WAREHOUSE": {
        # 仓库人员：管理出库流程、报告问题
        PipelineStatusType.IN_OUTBOUND,
        PipelineStatusType.OUTBOUND_COMPLETED,
        PipelineStatusType.ISSUE_REPORTED,
    },
    "ADMIN": {
        # 管理员：所有权限
        "*",
    },
}


# 状态优先级 - 用于判断是否为回退操作
PIPELINE_STATUS_PRIORITY = {
    PipelineStatusType.DRAFT: 0,
    PipelineStatusType.ORDER_CONFIRMED: 1,
    PipelineStatusType.IN_PURCHASE: 2,
    PipelineStatusType.PURCHASE_COMPLETED: 3,
    PipelineStatusType.IN_PRODUCTION: 2,
    PipelineStatusType.PRODUCTION_COMPLETED: 3,
    PipelineStatusType.IN_PURCHASE_AND_PRODUCTION: 2,
    PipelineStatusType.PURCHASE_AND_PRODUCTION_COMPLETED: 3,
    PipelineStatusType.IN_OUTBOUND: 4,
    PipelineStatusType.OUTBOUND_COMPLETED: 5,
    PipelineStatusType.COMPLETED: 99,
    PipelineStatusType.CANCELLED: 99,
    PipelineStatusType.ISSUE_REPORTED: 99,
}


# 权限分组 - 用于基于角色的可见性和可编辑性控制
class PipelineStatus:
    """Pipeline status groups for permission & visibility"""

    # Production 角色可见的状态
    PRODUCTION_VISIBLE = {
        PipelineStatusType.ORDER_CONFIRMED,
        PipelineStatusType.IN_PRODUCTION,
        PipelineStatusType.PRODUCTION_COMPLETED,
        PipelineStatusType.IN_OUTBOUND,
        PipelineStatusType.OUTBOUND_COMPLETED,
        PipelineStatusType.COMPLETED,
        PipelineStatusType.CANCELLED,
        PipelineStatusType.ISSUE_REPORTED,
    }

    # Production 角色可编辑的状态
    PRODUCTION_EDITABLE = {
        PipelineStatusType.ORDER_CONFIRMED,
        PipelineStatusType.IN_PRODUCTION,
    }

    # Warehouse 角色可见的状态
    WAREHOUSE_VISIBLE = {
        PipelineStatusType.PRODUCTION_COMPLETED,
        PipelineStatusType.PURCHASE_COMPLETED,
        PipelineStatusType.IN_OUTBOUND,
        PipelineStatusType.OUTBOUND_COMPLETED,
        PipelineStatusType.COMPLETED,
        PipelineStatusType.CANCELLED,
        PipelineStatusType.ISSUE_REPORTED,
    }

    # Warehouse 角色可编辑的状态
    WAREHOUSE_EDITABLE = {
        PipelineStatusType.PRODUCTION_COMPLETED,
        PipelineStatusType.PURCHASE_COMPLETED,
        PipelineStatusType.IN_OUTBOUND,
    }

    # Purchase 角色可见的状态
    PURCHASE_VISIBLE = {
        PipelineStatusType.ORDER_CONFIRMED,
        PipelineStatusType.IN_PURCHASE,
        PipelineStatusType.PURCHASE_COMPLETED,
        PipelineStatusType.IN_PRODUCTION,
        PipelineStatusType.PRODUCTION_COMPLETED,
        PipelineStatusType.IN_OUTBOUND,
        PipelineStatusType.OUTBOUND_COMPLETED,
        PipelineStatusType.COMPLETED,
        PipelineStatusType.CANCELLED,
        PipelineStatusType.ISSUE_REPORTED,
    }

    # Purchase 角色可编辑的状态
    PURCHASE_EDITABLE = {
        PipelineStatusType.ORDER_CONFIRMED,
        PipelineStatusType.IN_PURCHASE,
    }


# 角色与 PipelineType 的访问权限映射
class PipelineTypeAccess:
    """Pipeline type access groups for role-based filtering"""

    # Production 角色可见的 pipeline types (只关注有生产环节的流程)
    PRODUCTION_VISIBLE = {
        PipelineType.PRODUCTION_FLOW,
        PipelineType.HYBRID_FLOW,
    }

    # Warehouse 角色可见的 pipeline types (所有类型都需要出库)
    WAREHOUSE_VISIBLE = {
        PipelineType.PRODUCTION_FLOW,
        PipelineType.PURCHASE_FLOW,
        PipelineType.HYBRID_FLOW,
    }

    # Purchase 角色可见的 pipeline types (只关注有采购环节的流程)
    PURCHASE_VISIBLE = {
        PipelineType.PURCHASE_FLOW,
        PipelineType.HYBRID_FLOW,
    }
