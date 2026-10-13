# 🌊 FloodView

**Geo-tagged flood ground truthing from a phone.** Every photo records where you stand, where the camera looks, the patch of ground or water it sees, and what the water is doing. Built to collect field truth for flood maps (for example Sentinel-1 SAR or optical flood extents).

**Version 1.0.0** · Sibling of [CropView](https://github.com/somdeepkundu/cropview-v3) · MIT License

* **[Open FloodView](https://somdeepkundu.github.io/floodview/)**: the capture app (phone)
* **[Open FloodView Explorer](https://somdeepkundu.github.io/floodview/explorer.html)**: map, review and export your ZIPs (phone or desktop)

---

## In the field

1. Open the app, grant **camera, location and motion sensors**, and name the survey.
2. Set the **camera height**: the phone's height above the ground, or **above the water surface** if you are standing in water, on a boat or on a bridge (standing ≈ 1.4–1.6 m).
3. Set the tags that apply. They stay on for every capture until you change them:
   * **Depth** on a body scale (ankle · knee · waist · chest · above head) or a measured value in cm
   * **Flow**: still · slow · fast
   * **Level trend**: rising · steady · receding
   * **What's flooded**: cropland · road · settlement · open land · trees/grass · river/pond (normal water)
4. Aim and tap **FLOODED**, **WATERLOGGED** or **DRY**. One tap saves the photo with that class.
5. To trace the flood boundary, switch on **〰 Edge** and put the **crosshair on the waterline**. FloodView stores where the crosshair lands, so you can mark the edge from dry ground.
6. Export a **ZIP** from the Data tab (or **Share ZIP** straight to WhatsApp, Drive, etc.) and open it in the Explorer.

> ⚠ **Stay safe.** Never wade into moving water: 15 cm of fast water can knock an adult over and 30 cm can carry a car away. Tag from dry ground. The crosshair point exists so you don't have to stand in the water.

Captures can be edited later in the Data tab (class, tags, edge flag, note).

### Works offline

Open the app once with internet and it then works with no network: the app, its libraries and the font are cached, and map tiles you have already looked at stay available. Photos are stored on the phone (IndexedDB) at full resolution, so they survive a reload or a closed tab. You can also continue a saved survey later from the start screen. Tip: **Add to Home screen** for a full-screen app.

## What each capture records

| Field | Meaning |
|---|---|
| `flood_class` | `flooded` · `waterlogged` · `dry` |
| `water_depth_class` / `water_depth_cm` / `water_depth_source` | body-scale class; measured cm, or the class's typical value (`measured` · `body_scale` · `dry_class`) |
| `flow`, `level_trend` | `still`/`slow`/`fast`; `rising`/`steady`/`receding` |
| `flooded_land_cover` | `;`-separated: `cropland`, `road`, `settlement`, `open_land`, `vegetation`, `water_body` |
| `water_edge` | `true` marks the flood boundary |
| `heading_deg` | camera look direction, clockwise from true north (CropView's rotation-matrix heading) |
| `tilt_deg_from_nadir` | 0° = straight down, 90° = horizon |
| `aim_lat`, `aim_lon`, `aim_dist_m` | where the crosshair met the ground/water: `camera_height_m · tan(tilt)` ahead |
| `aim_uncertainty_m` | geometry-only ± for a 2° tilt and 10° heading error (add `gps_accuracy_m`) |
| footprint polygon | the camera's field of view projected on the ground/water |
| `note`, `edited` | free text, and when the capture was last edited |

The crosshair point is most reliable with the camera tilted **40°–80° from straight down** (the green band on the tilt bar). Near the horizon a small tilt error moves it by metres, and the HUD turns amber.

## The ZIP

```
images/   {Survey}_{ID}_{UTC time}_{lat}_{lon}.jpg
data/     {Survey}_captures_points.geojson       one point per photo, all fields above
          {Survey}_captures_footprints.geojson   footprint polygon per photo
          {Survey}_water_edge.geojson            edge points + traced edge lines
          {Survey}_captures.csv
README.txt
```

All GeoJSON opens directly in QGIS. Edge lines join edge points in capture order and break after a gap of more than 150 m or 20 minutes. File and field names follow CropView where the meaning is the same, so the **CropView Data Explorer can also read FloodView ZIPs**, and the **FloodView Explorer reads CropView ZIPs**.

## Explorer

* Open any number of ZIPs; each survey gets its own colour.
* Colour points by **flood class, depth, flow, level trend, capture time**, survey, look direction or tilt.
* Layers: footprints, crosshair points, **water-edge trace**, look-direction arrows, field-of-view cones, walking path.
* Show/hide classes, or only water-edge points. Full-screen photos with pinch/scroll zoom and swipe.
* **Review** tab: correct class, depth and edge flags in a table, on the map or in the photo viewer, and bulk-edit selections. The original field labels are kept (`field_flood_class`, `field_water_depth_class`, `field_water_edge`, `review_changed`), so every change stays traceable. Edits are saved in the browser and re-applied when you reopen the same ZIPs.
* Export reviewed points (GeoJSON), water edges (GeoJSON) and a CSV.

## For developers

* Two self-contained pages: `index.html` (capture) and `explorer.html`. No build step; GitHub Pages serves the repo root.
* Libraries are vendored in `vendor/` (Leaflet 1.9.4, JSZip 3.10.1, Comfortaa) so nothing loads from a CDN and the app works offline.
* `sw.js` is the offline cache. **Bump `VERSION` in `sw.js` whenever any file changes**, or phones keep the old copy.
* The compass and tilt pipeline (`cameraHeading`, `fuseHeading`, the watchdog, the Chrome 151 permission fix, …) is CropView v3.6's code, copied unchanged. turf.js was replaced by three small spherical-geodesy functions using turf's formulas and earth radius, verified identical to turf 6.5.

---

Developed by **Somdeep Kundu**, RuDRA Lab, C-TARA, IIT Bombay · [somdeepkundu.github.io](https://somdeepkundu.github.io)
© 2026 Somdeep Kundu · MIT License
