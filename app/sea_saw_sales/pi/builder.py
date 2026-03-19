"""Template sheet copy helpers (adapted from order_files/src/builder.py)."""

from copy import deepcopy


def shift_images_down(ws, from_row_1based, row_shift):
    """Shift all images anchored at or below from_row_1based downward."""
    from openpyxl.drawing.spreadsheet_drawing import TwoCellAnchor, OneCellAnchor
    threshold = from_row_1based - 1  # convert to 0-based
    for img in ws._images:
        a = img.anchor
        if isinstance(a, TwoCellAnchor):
            if a._from.row >= threshold:
                a._from.row += row_shift
                a._to.row += row_shift
        elif isinstance(a, OneCellAnchor):
            if a._from.row >= threshold:
                a._from.row += row_shift


def fix_copied_sheet(template_ws, ws, cfg):
    """Re-apply page setup and drawings that copy_worksheet omits."""
    ws.page_setup.paperSize = template_ws.page_setup.paperSize
    ws.page_setup.scale = template_ws.page_setup.scale
    ws.page_setup.orientation = template_ws.page_setup.orientation

    m = template_ws.page_margins
    for attr in ("left", "right", "top", "bottom", "header", "footer"):
        setattr(ws.page_margins, attr, getattr(m, attr))

    ws.print_area = template_ws.print_area or "A1:J37"
    ws.sheet_view.view = "pageBreakPreview"
    ws.sheet_view.zoomScale = 60
    ws.sheet_view.zoomScaleNormal = 100

    for img in template_ws._images:
        img_copy = deepcopy(img)
        if cfg.stamp_col_shift:
            _shift_image_cols(img_copy, cfg.stamp_col_shift)
        ws._images.append(img_copy)


def _shift_image_cols(img, col_shift):
    from openpyxl.drawing.spreadsheet_drawing import (
        TwoCellAnchor, OneCellAnchor, AbsoluteAnchor,
    )
    EMU_PER_COL = 914400
    a = img.anchor
    if isinstance(a, TwoCellAnchor):
        a._from.col += col_shift
        a._to.col += col_shift
    elif isinstance(a, OneCellAnchor):
        a._from.col += col_shift
    elif isinstance(a, AbsoluteAnchor):
        a.pos.x += col_shift * EMU_PER_COL
