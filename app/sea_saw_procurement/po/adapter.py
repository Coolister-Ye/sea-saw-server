"""Map a PurchaseOrder model instance to the PO generator's data format."""

from django.conf import settings
from sea_saw_export.utils import format_payment_terms, format_bank_details


def purchase_order_to_po_data(purchase_order) -> tuple:
    """
    Map a PurchaseOrder instance to (header dict, products list) for the PO generator.

    In a PO:
    - Buyer = our company (settings)
    - Seller = supplier
    """
    supplier = purchase_order.supplier
    seller_name = supplier.account_name if supplier else ""
    seller_address = (supplier.address or "") if supplier else ""

    currency = purchase_order.currency or "USD"

    header = {
        "Invoice No": f"PO-{purchase_order.purchase_code}",
        "Issue Date": purchase_order.purchase_date,
        "Buyer Name": getattr(settings, "PI_SELLER_NAME", ""),
        "Buyer Address": getattr(settings, "PI_SELLER_ADDRESS", ""),
        "Seller Name": seller_name,
        "Seller Address": seller_address,
        "Shipper Name": seller_name,
        "Shipper Address": seller_address,
        "Port of Loading": purchase_order.loading_port or "",
        "Port of Destination": purchase_order.destination_port or "",
        "Date of Loading": str(purchase_order.etd) if purchase_order.etd else "",
        "Shipment Type": purchase_order.shipment_term or "",
        "Incoterms": purchase_order.inco_terms or "",
        "Currency": currency,
        "Payment Terms": format_payment_terms(currency, purchase_order.deposit, purchase_order.balance),
        "Bank Details": format_bank_details(purchase_order.bank_account),
        "Additional Info": purchase_order.comment or "",
    }

    products = [
        {
            "Product Name": item.product_name or "",
            "Specifications": item.specification or "",
            "Cartons": item.order_qty,
            "KG/Carton": float(item.gross_weight) if item.gross_weight else 0,
            "Unit Price (USD/KG)": float(item.unit_price) if item.unit_price else 0,
        }
        for item in purchase_order.purchase_items.all()
    ]

    return header, products
