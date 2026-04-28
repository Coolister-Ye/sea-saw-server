"""Shared Excel document configuration for PI/PO generation."""

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
        "title_party",          # "Seller" or "Buyer" — which party fills B2/B3 letterhead
    ],
    defaults=("Seller",),
)
