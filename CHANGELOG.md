# Changelog

The capture app (`index.html`) and the Explorer (`explorer.html`) share one version number, set in `package.json` and in `sw.js`.

## 1.0.0 — 2026-10-13

First release.

### Capture app
- One-tap capture by class: **Flooded**, **Waterlogged**, **Dry**.
- Sticky tags: water depth (body scale or measured cm), flow, level trend, what's flooded (multi-select).
- **Water-edge** mode: the crosshair point on the waterline is stored as the edge, and edges are traced into lines.
- **Crosshair point** for every capture (`aim_lat`/`aim_lon`, distance and ± uncertainty), so water can be tagged from a safe distance.
- Look direction, tilt, GPS smoothing and ground footprint taken from CropView v3.6. The sensor code is copied unchanged.
- Edit any capture afterwards (class, tags, edge, note).
- Photos are stored at full resolution in IndexedDB and survive reloads. Saved surveys can be resumed.
- Works offline (service worker; libraries and font vendored locally; visited map tiles cached).
- Export ZIP or **Share ZIP**, plus points, footprints, water-edge GeoJSON and CSV.
- Screen kept awake during a survey.
- GPS accuracy of 0 m (reported by some external-GNSS and mock-location apps) no longer turns the position into NaN.

### Explorer
- Multi-ZIP map of FloodView (and CropView) exports, coloured by flood class, depth, flow, trend, capture time, survey, look direction or tilt.
- Layers for footprints, crosshair points, water-edge trace, arrows, cones and walking path. Class filters.
- Review tab with an audit trail: original field labels are kept next to reviewed ones.
- Autosaved review edits are re-applied when the same ZIPs are reopened.
- Export reviewed points, water edges and CSV; reopen a reviewed GeoJSON.
- Photo viewer with zoom and swipe, from the CropView Data Explorer v2.2.
