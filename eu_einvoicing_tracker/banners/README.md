# Banner generation guide

These HTML files render at fixed pixel dimensions. Screenshot the page, save as PNG, drop into `static/description/`.

## How to screenshot

### Path 1 — Browser at exact viewport size

1. Open the file in Chrome / Edge / Brave
2. Press `F12` for DevTools → click the device toolbar icon (or `Ctrl+Shift+M`)
3. Set the viewport to the exact dimensions in the file's HTML comment (e.g. `1200 × 400`)
4. Set zoom to 100% (DevTools → "Responsive" → zoom selector)
5. Use the DevTools "Capture full size screenshot" command:
   - Press `Ctrl+Shift+P` inside DevTools
   - Type "capture full size screenshot" → Enter
6. Save as PNG with the recommended filename

### Path 2 — Windows Snip & Sketch (fastest)

1. Open the file in Chrome at any size
2. Press `Ctrl+0` for 100% zoom
3. Press `Win+Shift+S`
4. Drag the rectangle tight to the `.canvas` div's edges (it has a fixed pixel size, so the rendering is the same on any screen ≥ 1200px wide)
5. Save the PNG

### Path 3 — Headless Chrome / Puppeteer (for batch)

```bash
google-chrome --headless --disable-gpu --screenshot=01_hero.png --window-size=1200,400 file://path/to/01_hero.html
```

## Banner inventory

| File | Dimensions | Recommended use |
|---|---|---|
| `01_hero.html` | 1200×400 | apps.odoo.com main banner (replace `banner.png`) |
| `02_timeline.html` | 1200×600 | The 2026–2028 mandate calendar feature image |
| `03_dashboard_mockup.html` | 1200×600 | Stylized "this is what you'll get" image |
| `04_comparison.html` | 1200×600 | "vs. checking factsheets manually" image — drop mid-listing |

## Naming convention for final PNGs

Once screenshotted, save with these filenames into `eu_einvoicing_tracker/static/description/`:

```
banner.png                  ← from 01_hero
cover.png                   ← from 02_timeline
feature_timeline.png        ← from 02
feature_dashboard.png       ← from 03
feature_comparison.png      ← from 04
```

## Reuse for other channels

- **LinkedIn / Twitter / X**: 02 (timeline) is the "look how much is coming" hook
- **Reddit r/odoo launch post**: 03 (dashboard mockup) — visual proof of value in one image
- **Cold outbound to EU SME Odoo partners**: 04 (comparison) — "you don't have this; here's what it costs"
- **Your blog at entrophy.in**: rotate all four

## Edit policy

Self-contained: no external CSS, no JS beyond Tailwind CDN. Brand colors are inline:

- Aubergine `#714B67` — primary, gradients
- Pink `#e9b8d9` — accents, deadline pills
- Dark base `#0f0c14` — backgrounds

Search/replace those three if rebranding. The flag emojis 🇧🇪 🇫🇷 etc. render natively on Windows 11 / macOS / iOS — fine for screenshots. If exporting via headless Chrome on Linux, install `fonts-noto-color-emoji` first or the flags render as letter pairs (e.g. "BE", "FR").

## Mandate numbers used in these mocks

Day-counts ("232 d", "597 d", "109 d") are calculated from a snapshot date of **2026-05-13** — re-render the HTML or regenerate the screenshot if you ship the listing months later, because viewers will compare against today's date.

To refresh:
1. Edit the `<span class="font-mono">...</span>` numbers in `01_hero.html` and `03_dashboard_mockup.html`
2. Use: `(mandate_date - today).days` for each card
3. Re-screenshot
