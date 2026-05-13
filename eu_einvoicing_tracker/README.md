# EU E-Invoicing Mandate Tracker

Country-by-country EU e-invoicing mandate calendar for Odoo 18 Community, with deadline reminders and per-company readiness dashboard.

## What it does

- Ships a curated mandate dataset for **32 countries** (27 EU + Norway, Iceland, Liechtenstein, Switzerland, UK)
- Each entry covers: B2B + B2G dates, required format, transmission channel, legal authority, and which Odoo modules cover it
- Per-company dashboard surfaces only your country's upcoming mandates
- Daily cron sends in-app reminders at 180 / 90 / 30 / 7 days before each deadline (logged to `mail.thread`)
- Kanban + list + form views, filterable by status, readiness, and time-to-deadline

## Why this exists

The 2026–2030 EU e-invoicing rollout has 12+ country mandates landing on different dates with different formats and different Odoo coverage levels. Finance teams need a single source of truth for "what hits us, when, and what module do we need?"

## Status

- v18.0.1.0.0 — initial scaffold, 2026-05-13
- Mandate data is a snapshot. Re-verify against the [EC eInvoicing Country Factsheets](https://ec.europa.eu/digital-building-blocks/sites/spaces/DIGITAL/pages/467108874/) before relying on dates for compliance decisions.

## Roadmap

- v18.0.1.1.0 — EN 16931 schema validator on `account.move` send
- v18.0.1.2.0 — pretty HTML email digest (not just `message_post`)
- v18.0.1.3.0 — link out to a hosted public mandate calendar (entrophy.in/einvoicing)
- v18.0.2.0.0 — companion paid modules: `l10n_si_eslog_b2b` (Slovenia, $149), `l10n_sk_peppol_5corner` (Slovakia, $149)

## Install

```bash
# Place under your addons path
odoo-bin --update eu_einvoicing_tracker -d <dbname>
```

Requires: `base`, `mail`, `account`.

## Pre-publish checklist (apps.odoo.com)

- [ ] `static/description/icon.png` (140x140)
- [ ] `static/description/banner.png`
- [ ] Screenshots: dashboard kanban grouped by status, mandate list filtered by "my country", form view for one mandate, sample reminder in chatter
- [ ] Run `--test-enable` against a fresh DB
- [ ] Manifest `price`, `currency`, `author`, `support`, `website` verified
- [ ] Confirm no competing module on apps.odoo.com under name "EU E-Invoicing Mandate Tracker" or similar
- [ ] Confirm `Entrophy` publisher slot is set up

## License

OPL-1
