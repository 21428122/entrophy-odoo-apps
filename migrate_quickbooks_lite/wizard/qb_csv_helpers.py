"""Shared CSV decoding + column matching helpers for QuickBooks imports.

QuickBooks Online ships UTF-8 with BOM; QuickBooks Desktop often ships cp1252.
Headers vary between QBO and QBD and between modules within QB. The helpers
here keep the per-wizard import logic small and consistent.
"""
import base64
import csv
import io

from odoo import _
from odoo.exceptions import UserError


def norm(s):
    """Lower-case, strip, collapse whitespace. Safe on None."""
    return " ".join((s or "").strip().lower().split())


def decode_csv(b64_data, must_have_any=(), max_scan_rows=20):
    """Decode a base64-encoded CSV upload.

    Tries common QB encodings in order. Skips junk title rows that some QB
    exports prepend by scanning the first `max_scan_rows` lines for one that
    contains at least one of the strings in `must_have_any` (header sniff).
    Returns a csv.DictReader plus the raw row list (already consumed).
    """
    if not b64_data:
        raise UserError(_("Please upload a CSV file first."))
    raw = base64.b64decode(b64_data)
    text = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise UserError(_("Could not decode the file. Please save it as UTF-8 CSV."))

    lines = text.splitlines()
    header_idx = 0
    if must_have_any:
        needles = [n.lower() for n in must_have_any]
        for i, line in enumerate(lines[:max_scan_rows]):
            lo = line.lower()
            if any(n in lo for n in needles):
                header_idx = i
                break
    cleaned = "\n".join(lines[header_idx:])

    try:
        dialect = csv.Sniffer().sniff(cleaned[:4096], delimiters=",\t;")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(cleaned), dialect=dialect)
    if not reader.fieldnames:
        raise UserError(_("The CSV appears to be empty or unreadable."))
    rows = list(reader)
    return reader.fieldnames, rows


def map_headers(fieldnames, required, optional):
    """Resolve logical column names against actual CSV headers.

    `required` and `optional` are dicts of {logical_name: tuple_of_candidates}.
    Candidates are matched case-insensitively after `norm()`. Raises UserError
    if any required logical column is unmatched. Optional columns may be absent.
    """
    actual_norm = {fn: norm(fn) for fn in fieldnames}
    out = {}
    for logical, candidates in required.items():
        cset = {norm(c) for c in candidates}
        for fn, nf in actual_norm.items():
            if nf in cset:
                out[logical] = fn
                break
    missing = [k for k in required if k not in out]
    if missing:
        raise UserError(
            _("Required column(s) not found: %(missing)s. CSV headers were: %(found)s")
            % {"missing": ", ".join(missing), "found": ", ".join(fieldnames)}
        )
    for logical, candidates in optional.items():
        cset = {norm(c) for c in candidates}
        for fn, nf in actual_norm.items():
            if nf in cset:
                out[logical] = fn
                break
    return out


def get(row, mapping, logical, default=""):
    """Safe field accessor: returns '' if logical column isn't mapped."""
    col = mapping.get(logical)
    if not col:
        return default
    return (row.get(col) or "").strip()


def upgrade_footer(record_count, limit):
    """Standard 'Lite cap reached' log footer."""
    if record_count < limit:
        return []
    return [
        "",
        _("Hit the Lite edition limit of %d records per file.") % limit,
        _("The Pro edition removes the cap and adds invoices, bills, payments, "
          "journal entries, attachments, and direct API sync."),
    ]
