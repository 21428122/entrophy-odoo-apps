# Screenshot capture recipe

apps.odoo.com expects **real Odoo screenshots** — synthetic mockups get listings rejected. Capture these from your local Odoo with `eu_einvoicing_tracker` installed.

## Setup

1. **Install the module** — right-click `install.ps1` → Run with PowerShell as Administrator.
2. Wait for "DONE - eu_einvoicing_tracker installed" message.
3. Open Chrome / Edge / Brave at `http://localhost:8069` and login to the `sop_test` database.
4. **Switch your company's country to France** (or any EU country) so the "my country" filter has something to show:
   Settings → Users & Companies → Companies → open your company → set Country = France.

## What to capture

Save each PNG into `eu_einvoicing_tracker/static/description/`. Filenames matter for ordering on the listing page — apps.odoo.com sorts alphabetically.

| File | Size | What's on it |
| --- | --- | --- |
| `screenshot_01_dashboard.png` | 1280 × 720 | **E-Invoicing → Dashboard** — kanban grouped by status, "my country" filter active, France-related mandates visible (FR Sep 2026, FR Sep 2027 SMEs). |
| `screenshot_02_all_mandates.png` | 1280 × 720 | **E-Invoicing → Mandates** — full list view sorted by B2B date, default "Upcoming" filter on. Show at least 8 rows: BE, PL, HR, GR, DK, FR, ES, DE, SK, EE, NO etc. |
| `screenshot_03_mandate_form.png` | 1280 × 720 | One mandate in form view — open **France · B2B**. Show the Mandate group (scope, status, b2b_date, b2b_phase_note, legal_basis) AND the Technical group (format, channel, readiness, module hint). |
| `screenshot_04_under_90_days.png` | 1280 × 720 | List view with the **"Under 90 days"** filter applied — proves the deadline-urgency filtering. |
| `screenshot_05_chatter_reminder.png` | 1280 × 720 | A mandate form with a chatter reminder visible. To force one: open developer mode → Settings → Technical → Scheduled Actions → "EU E-Invoicing: send deadline reminders" → Run Manually. Then refresh a mandate that's within 180 days. |

## How to capture

- Use the browser at exactly **1280 × 720** (DevTools → device toolbar → Responsive → 1280 × 720). Apps.odoo.com renders cards at multiple sizes; this fits all of them cleanly.
- Set zoom to 100%. No browser chrome should be visible.
- For each shot, use Snip & Sketch (`Win+Shift+S` → Rectangle) and drag tightly inside the Odoo content area.
- Save as PNG, no compression artefacts.

## Don't ship

- Synthetic / mocked screenshots — they get the listing rejected.
- Screenshots with personal data or third-party themes — reviewers want stock Odoo chrome.
- Screenshots that look obviously empty (e.g. "my country" set to a country with no mandates).
