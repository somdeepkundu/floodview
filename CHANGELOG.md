# Changelog

The capture app (`index.html`) and the Explorer (`explorer.html`) share one version number, set in `package.json` and in `sw.js`.

## 1.1.0 — 2026-10-13

### Added
- **After-flood survey.** Choose *During flood* or *After flood* when you start a survey.
  - After flood, the buttons are **FLOOD MARK**, **DAMAGE** and **NOT FLOODED**.
  - Tags: flood mark height (body scale or cm), what is damaged (house, road, bridge, crops, embankment, well, power line, vehicle, livestock), how bad (minor / major / destroyed), mud and debris left, and how long the water stayed.
  - Edge mode traces the outer edge of the flood marks.
- New export fields: `survey_phase`, `was_flooded` (true/false for both survey types, so during- and after-flood points can be mapped together), `water_depth_kind`, `damage_type`, `damage_severity`, `debris_left`, `water_stayed`.
- Explorer: colour by *Was it flooded?*, *Damage: how bad* and *During / after flood*; counts of flood marks and damage reports; damage details in the popups, viewer and Review table.

## 1.0.2 — 2026-10-13

### Fixed
- Share ZIP on Android failed with "Permission denied": the share sheet must open right after a tap, and building the ZIP took longer. The first tap now builds the ZIP and the button changes to TAP TO SHARE; the next tap shares it at once.

## 1.0.1 — 2026-10-13

### Changed
- Explorer: satellite imagery (Esri World Imagery) is now the default basemap on the map, the Review map and the photo viewer's mini-map, so standing water shows under the points. Voyager and OpenStreetMap are still in the layer switcher.

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
