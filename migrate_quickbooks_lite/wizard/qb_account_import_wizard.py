import logging

from odoo import _, fields, models

from .qb_csv_helpers import decode_csv, get, map_headers, norm, upgrade_footer

_logger = logging.getLogger(__name__)

LITE_LIMIT = 100

# QuickBooks Account Type / Detail Type → Odoo account.account.account_type
# Covers QBO and QBD naming variants. Keys are normalized.
QB_TYPE_MAP = {
    # Banks & Cash
    "bank": "asset_cash",
    "cash on hand": "asset_cash",
    "checking": "asset_cash",
    "savings": "asset_cash",
    "money market": "asset_cash",
    # Receivables
    "accounts receivable": "asset_receivable",
    "accounts receivable (a/r)": "asset_receivable",
    "a/r": "asset_receivable",
    # Other Current Assets
    "other current asset": "asset_current",
    "other current assets": "asset_current",
    "inventory": "asset_current",
    "inventory asset": "asset_current",
    "prepaid expenses": "asset_current",
    "undeposited funds": "asset_current",
    # Fixed Assets
    "fixed asset": "asset_fixed",
    "fixed assets": "asset_fixed",
    "machinery & equipment": "asset_fixed",
    "vehicles": "asset_fixed",
    "buildings": "asset_fixed",
    "accumulated depreciation": "asset_fixed",
    # Other Assets
    "other asset": "asset_non_current",
    "other assets": "asset_non_current",
    "long-term investments": "asset_non_current",
    "security deposits": "asset_non_current",
    "goodwill": "asset_non_current",
    # Payables
    "accounts payable": "liability_payable",
    "accounts payable (a/p)": "liability_payable",
    "a/p": "liability_payable",
    # Credit Card
    "credit card": "liability_credit_card",
    # Current Liabilities
    "other current liability": "liability_current",
    "other current liabilities": "liability_current",
    "sales tax payable": "liability_current",
    "payroll liabilities": "liability_current",
    "loan payable": "liability_current",
    # Long-Term Liabilities
    "long term liability": "liability_non_current",
    "long-term liability": "liability_non_current",
    "long term liabilities": "liability_non_current",
    "long-term liabilities": "liability_non_current",
    "notes payable": "liability_non_current",
    # Equity
    "equity": "equity",
    "owner's equity": "equity",
    "owners equity": "equity",
    "retained earnings": "equity",
    "opening balance equity": "equity",
    "common stock": "equity",
    # Income
    "income": "income",
    "sales of product income": "income",
    "service/fee income": "income",
    "discounts/refunds given": "income",
    # Other Income
    "other income": "income_other",
    "interest earned": "income_other",
    # COGS
    "cost of goods sold": "expense_direct_cost",
    "cost of labor - cos": "expense_direct_cost",
    "cost of labor - cogs": "expense_direct_cost",
    "supplies & materials - cogs": "expense_direct_cost",
    "supplies & materials": "expense_direct_cost",
    # Expense
    "expense": "expense",
    "expenses": "expense",
    "advertising/promotional": "expense",
    "auto": "expense",
    "bank charges": "expense",
    "dues & subscriptions": "expense",
    "insurance": "expense",
    "legal & professional fees": "expense",
    "meals & entertainment": "expense",
    "office supplies": "expense",
    "rent or lease": "expense",
    "repair & maintenance": "expense",
    "supplies": "expense",
    "taxes & licenses": "expense",
    "travel": "expense",
    "utilities": "expense",
    "wages": "expense",
    # Other Expense
    "other expense": "expense",
    "depreciation": "expense_depreciation",
    "penalties & settlements": "expense",
}

CODE_START = {
    "asset_cash": 1000,
    "asset_receivable": 1100,
    "asset_current": 1200,
    "asset_non_current": 1700,
    "asset_prepayments": 1800,
    "asset_fixed": 1500,
    "liability_payable": 2000,
    "liability_credit_card": 2100,
    "liability_current": 2200,
    "liability_non_current": 2400,
    "equity": 3000,
    "equity_unaffected": 3900,
    "income": 4000,
    "income_other": 4900,
    "expense_direct_cost": 5000,
    "expense": 6000,
    "expense_depreciation": 6800,
}


def _resolve_account_type(qb_type, qb_detail_type):
    detail = norm(qb_detail_type)
    tp = norm(qb_type)
    if detail in QB_TYPE_MAP:
        return QB_TYPE_MAP[detail]
    if tp in QB_TYPE_MAP:
        return QB_TYPE_MAP[tp]
    if "receivable" in tp:
        return "asset_receivable"
    if "payable" in tp:
        return "liability_payable"
    if "bank" in tp or "cash" in tp:
        return "asset_cash"
    if "asset" in tp and "fixed" in tp:
        return "asset_fixed"
    if "asset" in tp:
        return "asset_current"
    if "credit card" in tp:
        return "liability_credit_card"
    if "liability" in tp and ("long" in tp or "non" in tp):
        return "liability_non_current"
    if "liability" in tp:
        return "liability_current"
    if "equity" in tp:
        return "equity"
    if "cogs" in tp or "cost of" in tp:
        return "expense_direct_cost"
    if "income" in tp or "revenue" in tp or "sales" in tp:
        return "income"
    if "expense" in tp:
        return "expense"
    return None


class QBAccountImportWizard(models.TransientModel):
    _name = "qb.account.import.wizard"
    _description = "Import Chart of Accounts from QuickBooks CSV"

    csv_file = fields.Binary(string="QuickBooks CSV", required=True)
    csv_filename = fields.Char(string="Filename")
    overwrite = fields.Boolean(
        string="Update existing accounts",
        default=False,
        help="If checked, accounts matched by code or name will be updated. "
        "If unchecked, existing accounts are skipped.",
    )
    log = fields.Text(string="Import Log", readonly=True)
    state = fields.Selection(
        [("draft", "Upload"), ("done", "Done")],
        default="draft",
    )

    def action_import(self):
        self.ensure_one()
        company = self.env.company
        fieldnames, rows = decode_csv(
            self.csv_file,
            must_have_any=("name", "account", "type"),
        )
        mapping = map_headers(
            fieldnames,
            required={
                "name": ("name", "account", "account name", "fullname"),
                "type": ("type", "account type"),
            },
            optional={
                "detail": ("detail type", "detail-type", "subtype", "sub type"),
                "description": ("description", "desc"),
                "code": ("number", "account number", "acct #", "acct no", "code"),
            },
        )

        created = updated = skipped = 0
        errors = []
        Account = self.env["account.account"]
        next_code = dict(CODE_START)

        capped = rows[:LITE_LIMIT]
        if len(rows) > LITE_LIMIT:
            errors.append(
                _("Lite edition imports up to %(limit)d accounts per file; your "
                  "file has %(have)d. Processing the first %(limit)d only.")
                % {"limit": LITE_LIMIT, "have": len(rows)}
            )

        for i, row in enumerate(capped, start=1):
            name = get(row, mapping, "name")
            if not name:
                continue

            qb_type = get(row, mapping, "type")
            qb_detail = get(row, mapping, "detail")
            description = get(row, mapping, "description")
            csv_code = get(row, mapping, "code")

            account_type = _resolve_account_type(qb_type, qb_detail)
            if not account_type:
                errors.append(_("Row %d (%s): unknown QuickBooks type '%s / %s'.")
                              % (i, name, qb_type, qb_detail))
                continue

            if csv_code and csv_code.isascii():
                code = csv_code
            else:
                code = str(next_code[account_type])
                next_code[account_type] += 1

            existing = Account.search(
                [("company_ids", "in", company.id), "|", ("code", "=", code), ("name", "=", name)],
                limit=1,
            )

            vals = {
                "name": name,
                "code": code,
                "account_type": account_type,
                "company_ids": [(4, company.id)],
            }
            if description:
                vals["note"] = description

            try:
                if existing:
                    if self.overwrite:
                        existing.write(vals)
                        updated += 1
                    else:
                        skipped += 1
                else:
                    Account.create(vals)
                    created += 1
            except Exception as e:  # noqa: BLE001
                errors.append(_("Row %d (%s): %s") % (i, name, e))
                _logger.exception("QB account import failed on row %d", i)

        log_lines = [
            _("Imported %d new accounts.") % created,
            _("Updated %d existing accounts.") % updated,
            _("Skipped %d existing accounts.") % skipped,
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
