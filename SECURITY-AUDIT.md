# Security check — FloodView 1.1.1 (13 Oct 2026)

A short, single-pass review in the style of the CropView audit (Cloudflare security-audit method: map what comes in, follow it to where it is used, confirm in a browser). Scope: `index.html` (capture), `explorer.html`, `sw.js`.

## What comes in from outside
| Input | Where it goes |
|---|---|
| ZIP / GeoJSON files opened in the Explorer (may come from anyone) | map popups, viewer, Review table, legend, exports |
| Saved review session (browser storage) | same as above |
| Survey name, notes typed in the app | list, exports |
| Camera, GPS, compass | numbers only |

## Results
| # | Finding | Risk | Status |
|---|---|---|---|
| 1 | Text from loaded files is shown on the page | Could inject code if not escaped | **OK** — every text value is escaped; IDs in buttons are JSON-quoted; class, flow, damage etc. are only used as lookup keys |
| 2 | CSV export: a note starting with `=`, `+`, `-`, `@` would run as a formula in Excel | Low | **Fixed** — such cells get a leading `'` (both apps) |
| 3 | No Content-Security-Policy | Defence in depth | **Fixed** — scripts only from this site; images only from this site and the three map tile servers; no forms, plugins or outside connections |
| 4 | Libraries loaded from CDNs | Supply chain | **OK** — Leaflet, JSZip and the font are copied into `vendor/` |
| 5 | Service worker | Cache poisoning | **OK** — caches this site and the three tile servers only |
| 6 | Very large or broken ZIP | Browser tab slows or errors | Accepted — files are opened by the user on their own device; errors are caught and shown |
| 7 | Photos and data | Privacy | **OK** — stay on the phone (IndexedDB); nothing is uploaded; no accounts, no tracking |

## Checked in a browser
All tests pass with the policy on: capture 38/38, after-flood 11/11, Explorer 26/26, offline 5/5, and no policy violations on either page.
