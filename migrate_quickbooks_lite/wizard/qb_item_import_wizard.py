import logging

from odoo import _, fields, models

from .qb_csv_helpers import decode_csv, get, map_headers, norm, upgrade_footer

_logger = logging.getLogger(__name__)

LITE_LIMIT = 100

# QuickBooks Item Type → Odoo product.template.type
# Lite maps Inventory Part to 'consu' (Goods) without storable tracking.
# Pro flips is_storable=True and configures stock.location, valuation, etc.
QB_ITEM_TYPE_MAP = {
    "service": "service",
    "non-inventory": "consu",
    "non-inventory part": "consu",
    "non inventory part": "consu",
    "inventory": "consu",
    "inventory part": "consu",
    "inventory assembly": "consu",
    "other charge": "service",
    "discount": "service",
    "subtotal": "service",
    "group": "consu",
    "product": "consu",
    "goods": "consu",
}


def _parse_float(s):
    if not s:
        return 0.0
    s = str(s).strip()
    if not s:
        return 0.0
    # Strip currency symbols, commas, parentheses (negative), and whitespace
    negative = s.startswith("(") and s.endswith(")")
    cleaned = s.lstrip("$€£¥₹").replace(",", "").replace("(", "").replace(")", "").strip()
    try:
        val = float(cleaned)
        return -val if negative else val
    except ValueError:
        return 0.0


def _lookup_account(env, name_or_code):
    if not name_or_code:
        return False
    company = env.company
    domain = [("company_ids", "in", company.id),
              "|", ("name", "=ilike", name_or_code), ("code", "=", name_or_code)]
    return env["account.account"].search(domain, limit=1).id


class QBItemImportWizard(models.TransientModel):
    _name = "qb.item.import.wizard"
    _description = "Import Items / Products from QuickBooks CSV"

    csv_file = fields.Binary(string="QuickBooks CSV", required=True)
    csv_filename = fields.Char(string="Filename")
    overwrite = fields.Boolean(
        string="Update existing products",
        default=False,
        help="Match by SKU (internal reference) first, then by name. If checked, "
        "existing products are updated; otherwise they are skipped.",
    )
    log = fields.Text(string="Import Log", readonly=True)
    state = fields.Selection(
        [("draft", "Upload"), ("done", "Done")],
        default="draft",
    )

    def action_import(self):
        self.ensure_one()
        fieldnames, rows = decode_csv(
            self.csv_file,
            must_have_any=("name", "item", "product", "type"),
        )
        mapping = map_headers(
            fieldnames,
            required={
                "name": ("name", "item", "item name", "product", "product name", "fullname"),
            },
            optional={
                "sku": ("sku", "internal reference", "manufacturer's part number", "mpn", "item number"),
                "type": ("type", "item type"),
                "description": ("description", "sales description", "purchase description"),
                "sales_price": ("sales price/rate", "sales price", "price", "rate", "unit price"),
                "cost": ("cost", "purchase cost", "unit cost"),
                "income_account": ("income account",),
                "expense_account": ("expense account", "purchase account", "cogs account"),
                "barcode": ("upc", "barcode"),
                "active": ("active", "is active", "status"),
                "category": ("category", "item category"),
            },
        )

        created = updated = skipped = 0
        errors = []
        Product = self.env["product.template"]

        capped = rows[:LITE_LIMIT]
        if len(rows) > LITE_LIMIT:
            errors.append(
                _("Lite edition imports up to %(limit)d products; your file has "
                  "%(have)d. Processing the first %(limit)d only.")
                % {"limit": LITE_LIMIT, "have": len(rows)}
            )

        for i, row in enumerate(capped, start=1):
            name = get(row, mapping, "name")
            if not name:
                continue

            qb_type = norm(get(row, mapping, "type"))
            odoo_type = QB_ITEM_TYPE_MAP.get(qb_type, "consu")

            sku = get(row, mapping, "sku")
            description = get(row, mapping, "description")
            sales_price = _parse_float(get(row, mapping, "sales_price"))
            cost = _parse_float(get(row, mapping, "cost"))
            barcode = get(row, mapping, "barcode")
            income_acct_id = _lookup_account(self.env, get(row, mapping, "income_account"))
            expense_acct_id = _lookup_account(self.env, get(row, mapping, "expense_account"))

            vals = {
                "name": name,
                "type": odoo_type,
                "list_price": sales_price,
                "standard_price": cost,
            }
            if sku:
                vals["default_code"] = sku
            if description:
                vals["description_sale"] = description
            if barcode:
                vals["barcode"] = barcode
            if income_acct_id:
                vals["property_account_income_id"] = income_acct_id
            if expense_acct_id:
                vals["property_account_expense_id"] = expense_acct_id

            active_raw = norm(get(row, mapping, "active"))
            if active_raw and active_raw in {"no", "n", "false", "0", "inactive"}:
                vals["active"] = False

            existing = False
            if sku:
                existing = Product.search([("default_code", "=", sku)], limit=1)
            if not existing:
                existing = Product.search([("name", "=ilike", name)], limit=1)

            try:
                if existing:
                    if self.overwrite:
                        existing.write(vals)
                        updated += 1
                    else:
                        skipped += 1
                else:
                    Product.create(vals)
                    created += 1
            except Exception as e:  # noqa: BLE001
                errors.append(_("Row %d (%s): %s") % (i, name, e))
                _logger.exception("QB item import failed on row %d", i)

        log_lines = [
            _("Imported %d new products.") % created,
            _("Updated %d existing products.") % updated,
            _("Skipped %d existing products.") % skipped,
            "",
            _("Note: Inventory Part items from QuickBooks were imported as Goods "
              "(non-stock-tracked). To enable stock tracking, edit each product "
              "and toggle 'Track Inventory'. Pro edition handles this automatically."),
        ]
        if errors:
            log_lines.append("")
            log_lines.append(_("Issues (%d):") % len(errors))
            log_lines.extend(errors[:50])
            if len(errors) > 50:
                log_lines.append(_("... and %d more.") % (len(errors) - 50))
        log_lines.extend(upgrade_footer(len(capped), LITE_LIMIT))

        self.write({"log": "\n".join(log_lines), "state": "done"})
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
