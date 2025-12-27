ORDER_STATE_MACHINE = {
    "draft": {"order_confirmed", "cancelled"},
    "order_confirmed": {"in_production", "issue_reported"},
    "in_production": {"production_completed", "issue_reported"},
    "production_completed": {"in_outbound", "issue_reported"},
    "in_outbound": {"outbound_completed", "issue_reported"},
    "outbound_completed": {"completed", "issue_reported"},
    "issue_reported": {"draft", "in_production", "in_outbound", "cancelled"},
}

ROLE_ALLOWED_TARGET_STATES = {
    "SALE": {"draft", "order_confirmed", "cancelled"},
    "PRODUCTION": {"in_production", "production_completed", "issue_reported"},
    "WAREHOUSE": {"in_outbound", "outbound_completed", "issue_reported"},
    "ADMIN": {"*"},
}
