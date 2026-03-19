"""PI generator configuration (adapted from order_files/src/config.py)."""

from collections import namedtuple

# First product row in the TEMPLATE sheet (1-based Excel row number)
PRODUCT_FIRST_ROW = 22

DocConfig = namedtuple(
    "DocConfig",
    [
        "template_sheet",       # sheet name in PI_template.xlsx
        "doc_title",            # title written to B4
        "stamp_col_shift",      # columns to shift stamp image rightward
        "template_slots",       # product rows already in the template
        "total_row_offset",     # row of the Total/SUM row with template_slots products
        "kg_per_carton",        # default weight formula multiplier
        "print_area_rows",      # bottom row of the print area (for default slot count)
        "buyer_sig_row_base",   # row for buyer name in signature block
        "bank_details_row_base",  # row for bank details content
    ],
)

PI_CONFIG = DocConfig(
    template_sheet="TEMPLATE",
    doc_title="PROFORMA INVOICE",
    stamp_col_shift=0,
    template_slots=1,
    total_row_offset=24,  # row 22 = product, row 23 = blank separator, row 24 = Total
    kg_per_carton=20,
    print_area_rows=38,
    buyer_sig_row_base=34,
    bank_details_row_base=29,
)
