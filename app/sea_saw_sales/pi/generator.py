"""Generate PI Excel file from an Order instance and return BytesIO."""

import os
from io import BytesIO

from openpyxl import load_workbook

from .builder import fix_copied_sheet
from .config import PI_CONFIG, PRODUCT_FIRST_ROW
from .writer import setup_product_rows, fill_product_row, fill_header

TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "templates", "PI_template.xlsx"
)


def generate_pi_xlsx(order) -> BytesIO:
    """
    Generate a Proforma Invoice XLSX for the given Order instance.
    Returns a BytesIO object ready to stream as a file response.
    """
    from .adapter import order_to_pi_data

    header, products = order_to_pi_data(order)

    wb = load_workbook(TEMPLATE_PATH, rich_text=True)
    template_ws = wb[PI_CONFIG.template_sheet]

    ws = wb.copy_worksheet(template_ws)
    fix_copied_sheet(template_ws, ws, PI_CONFIG)
    ws.title = f"PI-{order.order_code}"[:31]

    # Remove all sheets except the new one
    for name in list(wb.sheetnames):
        if name != ws.title:
            del wb[name]

    # Expand product rows and fill data
    n_products = max(len(products), 1)
    total_row = setup_product_rows(ws, n_products, PI_CONFIG)

    for i, product in enumerate(products):
        fill_product_row(ws, PRODUCT_FIRST_ROW + i, product, PI_CONFIG)

    fill_header(ws, header, total_row, PI_CONFIG)

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
