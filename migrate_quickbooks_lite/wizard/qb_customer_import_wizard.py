import logging

from odoo import _, fields, models

from .qb_csv_helpers import decode_csv, get, map_headers, upgrade_footer

_logger = logging.getLogger(__name__)

LITE_LIMIT = 100


def _lookup_country(env, name):
    if not name:
        return False
    name = name.strip()
    # Common QB country aliases
    aliases = {"usa": "us", "u.s.a.": "us", "united states of america": "United States"}
    key = name.lower()
    if key in aliases:
        name = aliases[key]
    return env["res.country"].search(
        ["|", ("name", "=ilike", name), ("code", "=ilike", name)], limit=1
    ).id


def _lookup_state(env, name, country_id):
    if not name or not country_id:
        return False
    return env["res.country.state"].search(
        [("country_id", "=", country_id),
         "|", ("name", "=ilike", name), ("code", "=ilike", name)],
        limit=1,
    ).id


def _lookup_payment_term(env, name):
    if not name:
        return False
    return env["account.payment.term"].search(
        [("name", "=ilike", name)], limit=1
    ).id


class QBCustomerImportWizard(models.TransientModel):
    _name = "qb.customer.import.wizard"
    _description = "Import Customers from QuickBooks CSV"

    csv_file = fields.Binary(string="QuickBooks CSV", required=True)
    csv_filename = fields.Char(string="Filename")
    overwrite = fields.Boolean(
        string="Update existing customers",
        default=False,
        help="Match by email (preferred) or name. If checked, existing customers "
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
            must_have_any=("customer", "name", "company"),
        )
        mapping = map_headers(
            fieldnames,
            required={
                "name": ("customer", "name", "customer name", "display name", "fullname"),
            },
            optional={
                "company": ("company", "company name", "organization"),
                "email": ("email", "email address", "e-mail"),
                "phone": ("phone", "phone number", "main phone", "work phone"),
                "mobile": ("mobile", "mobile phone", "cell"),
                "street": ("street", "billing street", "billing address line 1", "address", "billing address"),
                "street2": ("street 2", "billing street 2", "billing address line 2"),
                "city": ("city", "billing city"),
                "state": ("state", "billing state", "province", "billing province"),
                "zip": ("zip", "billing zip", "postal code", "billing postal code", "postcode"),
                "country": ("country", "billing country"),
                "website": ("website", "web site", "url"),
                "terms": ("terms", "payment terms"),
                "notes": ("notes", "note", "memo"),
                "ref": ("ref", "customer id", "external id"),
                "tax_id": ("tax id", "tax number", "vat", "ein", "tin"),
            },
        )

        created = updated = skipped = 0
        errors = []
        Partner = self.env["res.partner"]

        capped = rows[:LITE_LIMIT]
        if len(rows) > LITE_LIMIT:
            errors.append(
                _("Lite edition imports up to %(limit)d customers; your file has "
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
                "customer_rank": 1,
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
                vals["property_payment_term_id"] = term_id
            notes = get(row, mapping, "notes")
            if notes:
                vals["comment"] = notes
            ref = get(row, mapping, "ref")
            if ref:
                vals["ref"] = ref
            tax_id = get(row, mapping, "tax_id")
            if tax_id:
                vals["vat"] = tax_id

            existing = False
            if email:
                existing = Partner.search([("email", "=ilike", email), ("customer_rank", ">=", 1)], limit=1)
            if not existing:
                existing = Partner.search([("name", "=ilike", display_name), ("customer_rank", ">=", 1)], limit=1)

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
                _logger.exception("QB customer import failed on row %d", i)

        log_lines = [
            _("Imported %d new customers.") % created,
            _("Updated %d existing customers.") % updated,
            _("Skipped %d existing customers.") % skipped,
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
