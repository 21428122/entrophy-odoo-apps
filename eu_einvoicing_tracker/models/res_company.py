from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    einvoicing_mandate_ids = fields.One2many(
        'eu.einvoicing.mandate',
        compute='_compute_einvoicing_mandate_ids',
        string='Mandates for this company',
    )
    einvoicing_next_deadline = fields.Date(
        compute='_compute_einvoicing_next_deadline',
        string='Next e-invoicing deadline',
    )
    einvoicing_days_to_next = fields.Integer(
        compute='_compute_einvoicing_next_deadline',
        string='Days to next deadline',
    )

    @api.depends('country_id')
    def _compute_einvoicing_mandate_ids(self):
        Mandate = self.env['eu.einvoicing.mandate']
        for company in self:
            if not company.country_id:
                company.einvoicing_mandate_ids = Mandate
                continue
            company.einvoicing_mandate_ids = Mandate.search([
                ('country_id', '=', company.country_id.id),
            ])

    @api.depends('einvoicing_mandate_ids.b2b_date')
    def _compute_einvoicing_next_deadline(self):
        today = fields.Date.context_today(self)
        for company in self:
            upcoming = company.einvoicing_mandate_ids.filtered(
                lambda m: m.b2b_date and m.b2b_date >= today
            ).sorted('b2b_date')
            if upcoming:
                company.einvoicing_next_deadline = upcoming[0].b2b_date
                company.einvoicing_days_to_next = (upcoming[0].b2b_date - today).days
            else:
                company.einvoicing_next_deadline = False
                company.einvoicing_days_to_next = 0
