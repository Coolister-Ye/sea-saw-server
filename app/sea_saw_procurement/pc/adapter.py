"""Map a PurchaseOrder model instance to the Purchase Contract generator's data format."""

from django.conf import settings
from sea_saw_export.utils import format_payment_terms, format_bank_details


def purchase_order_to_pc_data(purchase_order) -> tuple:
    """
    Map a PurchaseOrder instance to (header dict, products list) for the PC generator.

    In a Purchase Contract:
    - Buyer = our company (settings)
    - Seller = supplier
    """
    buyer = purchase_order.buyer
    buyer_name = (buyer.account_name if buyer else None) or getattr(
        settings, "PC_BUYER_NAME", ""
    )
    buyer_address = (buyer.address if buyer else None) or getattr(
        settings, "PC_BUYER_ADDRESS", ""
    )

    supplier = purchase_order.supplier
    seller_name = supplier.account_name if supplier else ""
    seller_address = (supplier.address or "") if supplier else ""

    shipper = purchase_order.shipper
    shipper_name = (shipper.account_name if shipper else None) or seller_name
    shipper_address = (shipper.address if shipper else None) or seller_address

    currency = purchase_order.currency or "USD"
    payment_terms = purchase_order.payment_terms or format_payment_terms(
        currency, purchase_order.deposit, purchase_order.balance
    )

    header = {
        "Invoice No": f"{purchase_order.purchase_code}",
        "Issue Date": purchase_order.purchase_date,
        "Buyer Name": buyer_name,
        "Buyer Address": buyer_address,
        "Seller Name": seller_name,
        "Seller Address": seller_address,
        "Shipper Name": shipper_name,
        "Shipper Address": shipper_address,
        "Port of Loading": purchase_order.loading_port or "",
        "Port of Destination": purchase_order.destination_port or "",
        "Date of Loading": str(purchase_order.etd) if purchase_order.etd else "",
        "Shipment Type": (purchase_order.shipment_term or "").upper(),
        "Incoterms": purchase_order.inco_terms or "",
        "Currency": currency,
        "Payment Terms": payment_terms,
        "Bank Details": format_bank_details(purchase_order.bank_account),
        "Additional Info": purchase_order.additional_info or "",
    }

    products = [
        {
            "Product Name": item.product_name or "",
            "Specifications": item.specification or "",
            "Cartons": item.purchase_qty,
            "KG/Carton": float(item.gross_weight) if item.gross_weight else 0,
            "Unit Price (USD/KG)": float(item.unit_price) if item.unit_price else 0,
        }
        for item in purchase_order.purchase_items.all()
    ]

    return header, products
