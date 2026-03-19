"""Map an Order model instance to the PI generator's data format."""

from django.conf import settings


def _format_payment_terms(order) -> str:
    """Build a readable payment terms string from deposit/balance amounts."""
    parts = []
    currency = order.currency or "USD"
    if order.deposit is not None:
        parts.append(f"Deposit: {currency} {order.deposit:,.2f}")
    if order.balance is not None:
        parts.append(f"Balance: {currency} {order.balance:,.2f}")
    return ", ".join(parts) if parts else ""


def order_to_pi_data(order) -> tuple:
    """
    Map an Order instance to (header dict, products list) for the PI generator.

    Returns:
        header: dict matching PI template header fields
        products: list of dicts, one per order item
    """
    account = order.account
    buyer_name = account.account_name if account else ""
    buyer_address = (account.address or "") if account else ""

    header = {
        "Invoice No": f"PI-{order.order_code}",
        "Issue Date": order.order_date,
        "Buyer Name": buyer_name,
        "Buyer Address": buyer_address,
        "Seller Name": getattr(settings, "PI_SELLER_NAME", ""),
        "Seller Address": getattr(settings, "PI_SELLER_ADDRESS", ""),
        "Shipper Name": getattr(settings, "PI_SHIPPER_NAME", ""),
        "Shipper Address": getattr(settings, "PI_SHIPPER_ADDRESS", ""),
        "Port of Loading": order.loading_port or "",
        "Port of Destination": order.destination_port or "",
        "Date of Loading": str(order.etd) if order.etd else "",
        "Shipment Type": order.shipment_term or "",
        "Incoterms": order.inco_terms or "",
        "Currency": order.currency or "USD",
        "Payment Terms": _format_payment_terms(order),
        "Bank Details": getattr(settings, "PI_BANK_DETAILS", ""),
        "Additional Info": order.comment or "",
    }

    products = [
        {
            "Product Name": item.product_name or "",
            "Specifications": item.specification or "",
            "Cartons": item.order_qty,
            "KG/Carton": float(item.gross_weight) if item.gross_weight else 0,
            "Unit Price (USD/KG)": float(item.unit_price) if item.unit_price else 0,
        }
        for item in order.order_items.all()
    ]

    return header, products
