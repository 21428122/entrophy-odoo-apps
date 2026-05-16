import logging

from odoo import _, fields, models

from .qb_csv_helpers import decode_csv, get, map_headers, upgrade_footer
from .qb_customer_import_wizard import _lookup_country, _lookup_state, _lookup_payment_term

_logger = logging.getLogger(__name__)

LITE_LIMIT = 100


def _truthy(s):
    """QB exports 1099 flags as 'Yes' / 'No' / 'TRUE' / 'FALSE' / 'Y' / 'N' / blank."""
    return (s or "").strip().lower() in {"yes", "y", "true", "1", "t", "x"}


class QBVendorImportWizard(models.TransientModel):
    _name = "qb.vendor.import.wizard"
    _description = "Import Vendors from QuickBooks CSV"

    csv_file = fields.Binary(string="QuickBooks CSV", required=True)
    csv_filename = fields.Char(string="Filename")
    overwrite = fields.Boolean(
        string="Update existing vendors",
        default=False,
        help="Match by email (preferred) or name. If checked, existing vendors "
        "are updated; otherwise they are skipped.",
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
            must_have_any=("vendor", "name", "supplier"),
        )
        mapping = map_headers(
            fieldnames,
            required={
                "name": ("vendor", "name", "vendor name", "supplier", "supplier name", "display name"),
            },
            optional={
                "company": ("company", "company name", "organization"),
                "email": ("email", "email address", "e-mail"),
                "phone": ("phone", "phone number", "main phone", "work phone"),
                "mobile": ("mobile", "mobile phone", "cell"),
                "street": ("street", "billing street", "address", "billing address"),
                "street2": ("street 2", "billing street 2"),
                "city": ("city", "billing city"),
                "state": ("state", "billing state", "province"),
                "zip": ("zip", "billing zip", "postal code", "postcode"),
                "country": ("country", "billing country"),
                "website": ("website", "web site", "url"),
                "terms": ("terms", "payment terms"),
                "notes": ("notes", "note", "memo", "account no", "account number"),
                "ref": ("ref", "vendor id", "external id"),
                "tax_id": ("tax id", "tax number", "vat", "ein", "tin"),
                "track_1099": ("track 1099", "1099", "is 1099", "1099 vendor"),
            },
        )

        created = updated = skipped = 0
        errors = []
        Partner = self.env["res.partner"]

        capped = rows[:LITE_LIMIT]
        if len(rows) > LITE_LIMIT:
            errors.append(
                _("Lite edition imports up to %(limit)d vendors; your file has "
                  "%(have)d. Processing the first %(limit)d only.")
                % {"limit": LITE_LIMIT, "have": len(rows)}
            )

        for i, row in enumerate(capped, start=1):
            name = get(row, mapping, "name")
            company_name = get(row, mapping, "company")
            display_name = company_name or name
            if not display_name:
                continue

            email = get(row, mapping, "email")
            country_id = _lookup_country(self.env, get(row, mapping, "country"))
            state_id = _lookup_state(self.env, get(row, mapping, "state"), country_id)
            term_id = _lookup_payment_term(self.env, get(row, mapping, "terms"))

            vals = {
                "name": display_name,
                "supplier_rank": 1,
                "is_company": bool(company_name),
                "company_type": "company" if company_name else "person",
            }
            if email:
                vals["email"] = email
            phone = get(row, mapping, "phone")
            if phone:
                vals["phone"] = phone
            mobile = get(row, mapping, "mobile")
            if mobile:
                vals["mobile"] = mobile
            street = get(row, mapping, "street")
            if street:
                vals["street"] = street
            street2 = get(row, mapping, "street2")
            if street2:
                vals["street2"] = street2
            city = get(row, mapping, "city")
            if city:
                vals["city"] = city
            if country_id:
                vals["country_id"] = country_id
            if state_id:
                vals["state_id"] = state_id
            zipc = get(row, mapping, "zip")
            if zipc:
                vals["zip"] = zipc
            website = get(row, mapping, "website")
            if website:
                vals["website"] = website
            if term_id:
                vals["property_supplier_payment_term_id"] = term_id
            notes_parts = []
            notes = get(row, mapping, "notes")
            if notes:
                notes_parts.append(notes)
            if _truthy(get(row, mapping, "track_1099")):
                notes_parts.append(_("Track 1099 / withholding: YES (carry over from QuickBooks)"))
            if notes_parts:
                vals["comment"] = "\n".join(notes_parts)
            ref = get(row, mapping, "ref")
            if ref:
                vals["ref"] = ref
            tax_id = get(row, mapping, "tax_id")
            if tax_id:
                vals["vat"] = tax_id

            existing = False
            if email:
                existing = Partner.search([("email", "=ilike", email), ("supplier_rank", ">=", 1)], limit=1)
            if not existing:
                existing = Partner.search([("name", "=ilike", display_name), ("supplier_rank", ">=", 1)], limit=1)

            try:
                if existing:
                    if self.overwrite:
                        existing.write(vals)
                        updated += 1
                    else:
                        skipped += 1
                else:
                    Partner.create(vals)
                    created += 1
            except Exception as e:  # noqa: BLE001
                errors.append(_("Row %d (%s): %s") % (i, display_name, e))
                _logger.exception("QB vendor import failed on row %d", i)

        log_lines = [
            _("Imported %d new vendors.") % created,
            _("Updated %d existing vendors.") % updated,
            _("Skipped %d existing vendors.") % skipped,
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
