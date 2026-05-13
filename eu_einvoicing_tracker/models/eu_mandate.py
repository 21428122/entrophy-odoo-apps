from odoo import api, fields, models
from odoo.tools.translate import _


MANDATE_STATUS = [
    ('live', 'Live'),
    ('upcoming', 'Upcoming'),
    ('b2g_only', 'B2G only'),
    ('proposed', 'Proposed'),
]


SCOPE = [
    ('b2b', 'B2B'),
    ('b2g', 'B2G'),
    ('b2c', 'B2C'),
]


READINESS = [
    ('first_party', 'First-party Odoo'),
    ('oca', 'OCA / Community'),
    ('partner', 'Third-party partner'),
    ('peppol_only', 'Peppol AP only'),
    ('gap', 'No module yet'),
]


class EuMandate(models.Model):
    _name = 'eu.einvoicing.mandate'
    _description = 'EU E-Invoicing Mandate'
    _inherit = ['mail.thread']
    _order = 'b2b_date, country_id'
    _rec_name = 'display_name'

    country_id = fields.Many2one(
        'res.country',
        required=True,
        ondelete='cascade',
    )
    country_code = fields.Char(related='country_id.code', store=True, index=True)
    display_name = fields.Char(compute='_compute_display_name', store=True)

    scope = fields.Selection(SCOPE, default='b2b', required=True)
    status = fields.Selection(MANDATE_STATUS, default='upcoming', required=True)

    b2g_date = fields.Date(string='B2G live since')
    b2b_date = fields.Date(string='B2B mandate date')
    b2b_phase_note = fields.Char(
        string='Phasing',
        help='Free-text on size-based phasing, tolerance periods, etc.',
    )

    format_label = fields.Char(string='Required format')
    channel_label = fields.Char(string='Transmission channel')
    legal_basis = fields.Char(string='Legal basis / authority')

    odoo_readiness = fields.Selection(READINESS, default='gap', required=True)
    odoo_module_hint = fields.Char(
        string='Suggested module(s)',
        help='Comma-separated technical names of Odoo modules covering this mandate.',
    )

    notes = fields.Text()
    source_url = fields.Char(string='Reference URL')

    days_to_deadline = fields.Integer(
        compute='_compute_days_to_deadline',
        store=False,
    )
    is_company_country = fields.Boolean(
        compute='_compute_is_company_country',
        search='_search_is_company_country',
    )

    _sql_constraints = [
        ('country_scope_uniq', 'unique(country_id, scope)',
         'Only one mandate row per country and scope.'),
    ]

    @api.depends('country_id', 'scope', 'b2b_date')
    def _compute_display_name(self):
        for rec in self:
            scope = dict(SCOPE).get(rec.scope, '')
            country = rec.country_id.name or '?'
            rec.display_name = f'{country} - {scope}'

    @api.depends('b2b_date')
    def _compute_days_to_deadline(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.b2b_date:
                rec.days_to_deadline = (rec.b2b_date - today).days
            else:
                rec.days_to_deadline = 0

    @api.depends_context('company')
    def _compute_is_company_country(self):
        company_country = self.env.company.country_id
        for rec in self:
            rec.is_company_country = (rec.country_id == company_country)

    def _search_is_company_country(self, operator, value):
        if operator not in ('=', '!='):
            return []
        company_country = self.env.company.country_id
        match = [('country_id', '=', company_country.id)] if company_country else []
        if (operator == '=' and value) or (operator == '!=' and not value):
            return match or [('id', '=', 0)]
        return [('country_id', '!=', company_country.id)] if company_country else []

    REMINDER_THRESHOLDS = (180, 90, 30, 7)

    @api.model
    def _cron_send_deadline_reminders(self):
        Reminder = self.env['eu.einvoicing.reminder']
        today = fields.Date.context_today(self)
        for company in self.env['res.company'].search([('country_id', '!=', False)]):
            mandates = self.search([
                ('country_id', '=', company.country_id.id),
                ('b2b_date', '>=', today),
            ])
            for mandate in mandates:
                days = (mandate.b2b_date - today).days
                for threshold in self.REMINDER_THRESHOLDS:
                    if days != threshold:
                        continue
                    already = Reminder.search_count([
                        ('mandate_id', '=', mandate.id),
                        ('company_id', '=', company.id),
                        ('threshold_days', '=', threshold),
                    ])
                    if already:
                        continue
                    self._post_reminder(company, mandate, threshold)
                    Reminder.create({
                        'mandate_id': mandate.id,
                        'company_id': company.id,
                        'threshold_days': threshold,
                    })

    def _post_reminder(self, company, mandate, threshold):
        partner_ids = []
        group = self.env.ref('account.group_account_manager', raise_if_not_found=False)
        if group:
            users = group.users.filtered(lambda u: company in u.company_ids)
            if users:
                partner_ids = users.mapped('partner_id').ids
        body = _(
            'E-invoicing mandate reminder for %(country)s (company: %(company)s): '
            'B2B deadline %(date)s (%(days)s days away). '
            'Required format: %(format)s. '
            'Channel: %(channel)s. '
            'Odoo readiness: %(readiness)s. '
            'Suggested modules: %(hint)s.'
        ) % {
            'country': mandate.country_id.name,
            'company': company.name,
            'date': mandate.b2b_date,
            'days': threshold,
            'format': mandate.format_label or '-',
            'channel': mandate.channel_label or '-',
            'readiness': dict(READINESS).get(mandate.odoo_readiness, '-'),
            'hint': mandate.odoo_module_hint or '-',
        }
        mandate.with_company(company).message_post(
            body=body,
            partner_ids=partner_ids,
            subject=_('E-invoicing deadline: %s (%s days)') % (mandate.country_id.name, threshold),
        )


class EuMandateReminder(models.Model):
    _name = 'eu.einvoicing.reminder'
    _description = 'Sent reminder log (to avoid duplicate emails)'

    mandate_id = fields.Many2one('eu.einvoicing.mandate', required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', required=True, ondelete='cascade')
    threshold_days = fields.Integer(required=True)
    sent_at = fields.Datetime(default=fields.Datetime.now)

    _sql_constraints = [
        ('reminder_uniq', 'unique(mandate_id, company_id, threshold_days)',
         'Reminder for this mandate/company/threshold already sent.'),
    ]
