"""Map an Order model instance to the PI generator's data format."""

from django.conf import settings
from sea_saw_export.utils import format_payment_terms, format_bank_details


def order_to_pi_data(order) -> tuple:
    """
    Map an Order instance to (header dict, products list) for the PI generator.

    Returns:
        header: dict matching PI template header fields
        products: list of dicts, one per order item
    """
    buyer = order.buyer
    buyer_name = buyer.account_name if buyer else ""
    buyer_address = (buyer.address or "") if buyer else ""

    seller = order.seller
    seller_name = (seller.account_name if seller else None) or getattr(
        settings, "PI_SELLER_NAME", ""
    )
    seller_address = (seller.address if seller else None) or getattr(
        settings, "PI_SELLER_ADDRESS", ""
    )

    shipper = order.shipper
    shipper_name = (shipper.account_name if shipper else None) or getattr(
        settings, "PI_SHIPPER_NAME", ""
    )
    shipper_address = (shipper.address if shipper else None) or getattr(
        settings, "PI_SHIPPER_ADDRESS", ""
    )

    currency = order.currency or "USD"
    payment_terms = order.payment_terms or format_payment_terms(
        currency, order.deposit, order.balance
    )

    header = {
        "Invoice No": f"{order.order_code}",
        "Issue Date": order.order_date,
        "Buyer Name": buyer_name,
        "Buyer Address": buyer_address,
        "Seller Name": seller_name,
        "Seller Address": seller_address,
        "Shipper Name": shipper_name,
        "Shipper Address": shipper_address,
        "Port of Loading": order.loading_port or "",
        "Port of Destination": order.destination_port or "",
        "Date of Loading": str(order.etd) if order.etd else "",
        "Shipment Type": (order.shipment_term or "").upper(),
        "Incoterms": order.inco_terms or "",
        "Currency": currency,
        "Payment Terms": payment_terms,
        "Bank Details": format_bank_details(
            order.bank_account, fallback_setting="PI_BANK_DETAILS"
        ),
        "Additional Info": order.additional_info or "",
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
