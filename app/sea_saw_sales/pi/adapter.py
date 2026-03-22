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


def _format_bank_details(bank_account) -> str:
    """Build a pipe-separated bank details string from a BankAccount instance."""
    if bank_account is None:
        return getattr(settings, "PI_BANK_DETAILS", "")

    parts = []
    if bank_account.account_holder:
        parts.append(f"Account Holder: {bank_account.account_holder}")
    if bank_account.bank_name:
        parts.append(f"Bank Name: {bank_account.bank_name}")
    if bank_account.account_number:
        parts.append(f"Account No: {bank_account.account_number}")
    if bank_account.swift_code:
        parts.append(f"SWIFT/BIC: {bank_account.swift_code}")
    if bank_account.branch:
        parts.append(f"Branch: {bank_account.branch}")
    if bank_account.bank_address:
        parts.append(f"Bank Address: {bank_account.bank_address}")
    return " | ".join(parts)


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
        "Bank Details": _format_bank_details(order.bank_account),
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
