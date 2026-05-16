{
    "name": "QuickBooks to Odoo Lite",
    "summary": "Import Chart of Accounts, Customers, Vendors, and Items from QuickBooks CSV exports",
    "description": """
Migrate from QuickBooks to Odoo - Lite Edition
================================================

Move QuickBooks master data into Odoo in minutes. No API setup, no
developer account, no credentials. Export CSV from QuickBooks, upload to
Odoo, review the auto-detected column mapping, click Import.

What this Lite edition imports
------------------------------
* Chart of Accounts (up to 100 accounts)
* Customers (up to 100 customers)
* Vendors (up to 100 vendors)
* Items / Products (up to 100 items)

Compatibility
-------------
* Odoo 18 Community and Enterprise
* QuickBooks Online (all tiers)
* QuickBooks Desktop Pro / Premier / Enterprise (via CSV export)
* QuickBooks Self-Employed (via CSV export)

Data privacy
------------
All processing happens inside your Odoo instance. No data is sent to any
external service. The module makes no outbound network calls.
""",
    "author": "Entrophy",
    "website": "https://migrate-to-odoo.com",
    "support": "entrophy9709@gmail.com",
    "category": "Accounting/Accounting",
    "version": "18.0.1.0.0",
    "license": "LGPL-3",
    "depends": [
        "account",
        "contacts",
        "product",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/qb_account_import_wizard_views.xml",
        "wizard/qb_customer_import_wizard_views.xml",
        "wizard/qb_vendor_import_wizard_views.xml",
        "wizard/qb_item_import_wizard_views.xml",
        "views/menu_views.xml",
    ],
    "images": [
        "static/description/banner.png",
    ],
    "application": True,
    "installable": True,
    "auto_install": False,
    "price": 0.0,
    "currency": "EUR",
}
