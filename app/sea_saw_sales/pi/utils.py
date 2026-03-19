"""Shared helper utilities (copied from order_files/src/utils.py)."""

import datetime


def parse_date(val):
    if isinstance(val, (datetime.datetime, datetime.date)):
        return val
    if isinstance(val, str) and val.strip():
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
            try:
                return datetime.datetime.strptime(val.strip(), fmt)
            except ValueError:
                pass
    return val


def specs_to_multiline(s):
    if not s:
        return ""
    return "\n".join(p.strip() for p in str(s).split("|"))


def safe_str(val):
    if val is None:
        return ""
    return str(val).strip().rstrip("\t")
