# Migrate from QuickBooks — Lite Edition

The free, friction-free way to move your QuickBooks master data into Odoo.

## What this module does

Imports the four pieces of master data that almost every QuickBooks migration starts with:

1. **Chart of Accounts** — every account, with type and code mapped to Odoo's account model
2. **Customers** — names, addresses, emails, payment terms
3. **Vendors** — names, addresses, emails, payment terms
4. **Items / Products** — services, inventory parts, non-inventory parts

No OAuth, no developer account, no API setup. Export CSV from QuickBooks (the
"Export to Excel" button is on every list page), upload to Odoo, review, import.

## What this module does NOT do

The Lite edition is intentionally limited to demonstrate the workflow. For
real migrations you'll want the Pro edition, which adds:

* **Unlimited records** (Lite is capped at 100 per category)
* **Invoices, Bills, Payments** — full transactional history
* **Journal entries** — manual GL postings, opening balances
* **Direct API sync** — OAuth into QuickBooks Online, no manual export
* **Multi-year historical data**
* **Sales tax mapping** (US/CA jurisdictions or QBO Automated Sales Tax)
* **Bank reconciliation status preservation**
* **Attachment migration** (PDFs on invoices, receipts)
* **Custom field mapping**
* **Items with three accounts** (Income, COGS, Asset) for Inventory Parts
* **Customer:Job hierarchy** → projects or partner hierarchy
* **Class & Location** → analytic accounts
* **Undeposited Funds handling** at cutover

Pro edition is sold separately on apps.odoo.com.

## Compatibility

* Odoo 18 Community and Enterprise
* QuickBooks Online (all tiers)
* QuickBooks Desktop Pro / Premier / Enterprise (via CSV export)
* QuickBooks Self-Employed

## Installation

1. Place this module in your Odoo addons path
2. Update the apps list
3. Install "Migrate from QuickBooks (Lite)"
4. The new menu "Migrate from QuickBooks" appears in the top bar

## Usage

### Chart of Accounts

1. In QuickBooks Online: Accounting → Chart of Accounts → "Run report" →
   Export → Export to Excel → save as CSV
2. In QuickBooks Desktop: Lists → Chart of Accounts → Reports menu →
   "Account Listing" → Excel → Create New Worksheet → save as CSV
3. In Odoo: Migrate from QuickBooks → Chart of Accounts → upload the CSV
4. Click Import. Review the log. Done.

The importer detects column headers automatically across QBO and QBD export
variants. It maps QuickBooks account types and detail types to the
corresponding Odoo `account.account.account_type`.

## License

LGPL-3 — free to use, modify, and redistribute. The Pro edition is sold
separately on apps.odoo.com under OPL-1.

## Author

Entrophy
