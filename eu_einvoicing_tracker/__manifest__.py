{
    'name': 'EU E-Invoicing Mandate Tracker',
    'version': '18.0.1.0.0',
    'summary': 'Country-by-country EU e-invoicing mandate calendar, deadline reminders, and EN 16931 readiness dashboard',
    'description': """
EU E-Invoicing Mandate Tracker
==============================

Know exactly when your country's e-invoicing mandate kicks in, what format
you must support, and whether your Odoo install is ready - across all 27 EU
member states plus Norway, Iceland, Liechtenstein, Switzerland, and the UK.

Features
--------
* Mandate calendar covering 32 countries with B2B + B2G dates, channels,
  and required formats (Peppol BIS 3.0, FatturaPA, KSeF, e-SLOG, XRechnung,
  Factur-X, VeriFactu, myDATA, RO e-Factura, NAV RTIR, OIOUBL, and more)
* Per-company readiness dashboard: which mandates apply to you, time-to-
  deadline, format support status, recommended next action
* Scheduled email reminders before each upcoming mandate hits
* EN 16931 schema validator on outgoing customer invoices (catch malformed
  UBL/CII before the tax authority does)
* Curated registry of which Odoo modules cover which country mandate
  (first-party, OCA, or partner)
* Lightweight - depends only on base, mail, and account
""",
    'author': 'Entrophy',
    'website': 'https://entrophy.in',
    'license': 'OPL-1',
    'category': 'Accounting/Localizations/EDI',
    'depends': ['base', 'mail', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/eu_mandates_data.xml',
        'data/ir_cron_data.xml',
        'views/mandate_views.xml',
        'views/dashboard_views.xml',
        'views/menus.xml',
    ],
    'images': [
        'static/description/banner.png',
        'static/description/cover.png',
    ],
    'price': 19.00,
    'currency': 'EUR',
    'support': 'udbhavkamath2424@gmail.com',
    'application': True,
    'installable': True,
}
