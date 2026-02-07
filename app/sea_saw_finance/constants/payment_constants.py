from sea_saw_finance.models import PaymentType

# 角色与 Payment Type 的访问权限映射
ROLE_PAYMENT_TYPE_ACCESS = {
    "ADMIN": {
        # ADMIN 可以访问所有类型的 payment
        PaymentType.ORDER_PAYMENT,
        PaymentType.PURCHASE_PAYMENT,
        PaymentType.PRODUCTION_PAYMENT,
        PaymentType.OUTBOUND_PAYMENT,
    },
    "SALE": {
        # SALE 可以管理订单收款和采购付款
        PaymentType.ORDER_PAYMENT,
        PaymentType.PURCHASE_PAYMENT,
    },
    "PRODUCTION": {
        # PRODUCTION 只能查看和管理生产费用
        PaymentType.PRODUCTION_PAYMENT,
    },
    "WAREHOUSE": {
        # WAREHOUSE 只能查看和管理物流费用
        PaymentType.OUTBOUND_PAYMENT,
    },
}
