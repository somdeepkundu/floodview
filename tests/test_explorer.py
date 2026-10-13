"""Headless end-to-end test of the FloodView Explorer.
Usage: python3 test_explorer.py <base_url> <shots_dir>   (expects shots/export.zip and shots/cropview_sample.zip)"""
import sys, json, os
from playwright.sync_api import sync_playwright
BASE, OUT = sys.argv[1], sys.argv[2]
FV, CV = OUT+'/export.zip', OUT+'/cropview_sample.zip'
if not os.path.exists(CV):   # a CropView v3.4-format ZIP (no flood fields), built from one FloodView photo
    import zipfile
    src=zipfile.ZipFile(FV); img=[n for n in src.namelist() if n.endswith('.jpg')][0]
    feat={"type":"Feature","geometry":{"type":"Point","coordinates":[74.2500,16.6950,560]},
      "properties":{"id":"CV-1791800000000","imgName":"Nashik_CV-1791800000000_20261012100000_16p69500_74p25000.jpg","timestamp":"2026-10-12T10:00:00.000Z","project":"Nashik_Crop",
      "heading_deg":200,"azimuth_deg":200,"heading_source":"COMPASS","tilt_deg_from_nadir":45,"tilt_deg":45,"camera_height_m":1.5,"hfov_deg":65,"gps_accuracy_m":4,"kc_stage":3,
      "footprint_width_m":2.1,"footprint_depth_m":1.9,"footprint_far_capped":False},
      "fov_polygon":{"type":"Polygon","coordinates":[[[74.25,16.6949],[74.2499,16.6948],[74.2501,16.6948],[74.25,16.6949]]]}}
    with zipfile.ZipFile(CV,'w') as z:
        z.writestr('data/Nashik_Crop_captures_points.geojson',json.dumps({"type":"FeatureCollection","metadata":{"app":"CropView L1","version":"3.4.0","project":"Nashik_Crop"},"features":[feat]}))
        z.writestr('images/'+feat['properties']['imgName'], src.read(img))
errors, failed_req, checks = [], [], []
def check(name, cond, detail=''):
    checks.append((name, bool(cond))); print(('PASS ' if cond else 'FAIL ') + name + (' — '+str(detail) if detail!='' else ''))

with sync_playwright() as p:
    b = p.chromium.launch(args=['--disable-gpu','--force-color-profile=srgb'])
    ctx = b.new_context(viewport={'width':1366,'height':860}, accept_downloads=True)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.on('requestfailed', lambda r: failed_req.append(r.url))
    pg.goto(BASE+'/explorer.html'); pg.wait_for_timeout(1200)
    pg.screenshot(path=OUT+'/x01_empty.png')
    pg.set_input_files('#file-in', [FV, CV]); pg.wait_for_timeout(2500)
    st = pg.evaluate("({n:captures.length, b:batches.map(x=>x.app+':'+x.name+':'+x.count+':'+x.imgCount), img:captures.filter(c=>c.imgUrl).length, cls:captures.map(c=>c.cls)})")
    check('6 points from 2 ZIPs... (4 FloodView + 1 CropView)', st['n']==5, st)
    check('apps detected', sorted(st['b'])==sorted(['FloodView:Kolhapur_Test__1:4:4','CropView:Nashik_Crop:1:1']), st['b'])
    check('photos linked', st['img']==5)
    check('CropView point unlabelled', st['cls'].count(None)==1)
    legend = pg.inner_text('#col-legend')
    check('class legend', 'Flooded' in legend and 'Waterlogged' in legend and 'Unlabelled' in legend, legend.replace('\n',' | '))
    lay = pg.evaluate("({edge:gEdge.getLayers().length, aim:gAim.getLayers().length, fp:gFP.getLayers().length, pts:gPts.getLayers().length})")
    check('layers: edge trace, aim points, footprints, points', lay['edge']==2 and lay['aim']>=4 and lay['fp']==5 and lay['pts']>=5, lay)
    stats = pg.evaluate("['st-n','st-fl','st-wl','st-dr','st-edge','st-depth'].map(i=>document.getElementById(i).textContent)")
    check('summary', stats[:5]==['5','2','2','0','2'] and stats[5]=='~45 cm', stats)
    pg.screenshot(path=OUT+'/x02_map.png')
    # colour modes all render without errors
    for m in ['depth','flow','trend','time','batch','azimuth','tilt','class']:
        pg.select_option('#sel-col', m); pg.wait_for_timeout(150)
        if m=='depth': pg.screenshot(path=OUT+'/x03_depth.png'); dl_txt=pg.inner_text('#col-legend')
        if m=='time': tl_txt=pg.inner_text('#col-legend')
    check('depth legend has cm ticks', 'cm' in dl_txt, dl_txt.replace('\n',' | '))
    check('time legend', 'Capture time' in tl_txt, tl_txt.replace('\n',' | ')[:120])
    # class filter: hide waterlogged
    pg.click('.cf:has-text("Waterlogged")'); pg.wait_for_timeout(200)
    check('class filter hides points', pg.evaluate("visibleCaps().length")==3)
    pg.click('.cf:has-text("Waterlogged")'); pg.wait_for_timeout(200)
    # open first flooded point in viewer + lightbox
    pg.evaluate("openViewer(captures.find(c=>c.cls==='flooded'))"); pg.wait_for_timeout(300)
    check('viewer shows class pill', 'FLOODED' in pg.inner_text('#viewer-top'))
    pg.click('#viewer-img'); pg.wait_for_timeout(700)
    pg.screenshot(path=OUT+'/x04_lightbox.png')
    check('lightbox details', 'Knee' in pg.inner_text('#lb-details-content'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(400)
    # REVIEW: change first point to waterlogged, mark CropView point dry, delete one, unmark an edge
    pg.click('.tabbtn[data-tab=review]'); pg.wait_for_timeout(800)
    rows = pg.locator('#rv-tbody tr.an-row')
    check('review table rows', rows.count()==5, rows.count())
    # rows are sorted by time: row0 = CropView (12 Oct), rows1..4 = FloodView
    rows.nth(0).locator('select').first.select_option('dry')
    pg.wait_for_timeout(200)
    rows = pg.locator('#rv-tbody tr.an-row')
    rows.nth(1).locator('select').first.select_option('waterlogged'); pg.wait_for_timeout(200)
    rows = pg.locator('#rv-tbody tr.an-row')
    rows.nth(2).locator('input[type=checkbox]').nth(1).uncheck(); pg.wait_for_timeout(200)
    rows = pg.locator('#rv-tbody tr.an-row')
    rows.nth(4).locator('button:has-text("Delete")').click(); pg.wait_for_timeout(300)
    pg.screenshot(path=OUT+'/x05_review.png')
    ch = pg.evaluate("captures.map(c=>({id:c.id,cls:c.cls,field:c.field.cls,edge:c.edge,fe:c.field.edge,del:c.deleted,changed:!!isChanged(c)}))")
    check('3 points changed, 1 deleted', sum(1 for c in ch if c['changed'])==3 and sum(1 for c in ch if c['del'])==1, ch)
    pg.evaluate("document.getElementById('rv-changed').click()"); pg.wait_for_timeout(200)
    check('changed-only filter', pg.locator('#rv-tbody tr.an-row').count()==3)
    pg.evaluate("document.getElementById('rv-changed').click()")
    # bulk: select shown, mark edge on all
    pg.click('text=Select shown'); pg.click('text=Unmark edge'); pg.wait_for_timeout(200)
    check('bulk unmark edge', pg.evaluate("activeCaps().filter(c=>c.edge).length")==0)
    pg.click('text=Clear')
    pg.evaluate("captures.filter(c=>c.field.edge).forEach(c=>c.edge=true); refreshReview(); redraw(); autosave()")   # put the field edges back, except the one unmarked above stays field-true
    # exports
    with pg.expect_download() as d1: pg.click('.an-toolbar .tbtn.primary')
    gj = json.load(open(d1.value.path()))
    props = [f['properties'] for f in gj['features']]
    cvp = [x for x in props if x['project']=='Nashik_Crop'][0]
    check('export: CropView point now dry, field label null, changed', cvp['flood_class']=='dry' and cvp['field_flood_class'] is None and cvp['review_changed'] and cvp['kc_stage']==3, cvp)
    fl_changed = [x for x in props if x['field_flood_class']=='flooded' and x['flood_class']=='waterlogged']
    check('export: flooded->waterlogged keeps field label', len(fl_changed)==1)
    check('export: deleted kept with flag', sum(1 for x in props if x['deleted'])==1)
    check('export: valid GeoJSON points', gj['type']=='FeatureCollection' and all(f['geometry']['type']=='Point' and len(f['geometry']['coordinates'])==2 for f in gj['features']))
    pg.click('.tabbtn[data-tab=map]'); pg.wait_for_timeout(500)
    with pg.expect_download() as d2: pg.click('text=Export water edges')
    eg = json.load(open(d2.value.path()))
    check('edge export: line + points', any(f['geometry']['type']=='LineString' for f in eg['features']) and sum(1 for f in eg['features'] if f['geometry']['type']=='Point')==2, [f['geometry']['type'] for f in eg['features']])
    with pg.expect_download() as d3: pg.click('text=Export table (CSV)')
    csv = open(d3.value.path()).read().strip().split('\n')
    check('csv: header + 4 active rows', len(csv)==5 and csv[0].startswith('id,project,timestamp'), len(csv))
    saved_path = OUT+'/reviewed.geojson'; open(saved_path,'w').write(json.dumps(gj))
    # reload: banner, then re-open the ZIPs -> saved edits re-applied automatically
    pg.wait_for_timeout(700)
    pg.reload(); pg.wait_for_timeout(1200)
    check('restore banner after reload', pg.is_visible('#restore-banner'))
    pg.set_input_files('#file-in', [CV, FV]); pg.wait_for_timeout(2500)
    after = pg.evaluate("captures.map(c=>({p:c.project,cls:c.cls,del:c.deleted,chg:!!isChanged(c)}))")
    check('edits re-applied when ZIPs reopened (different order)', sum(1 for c in after if c['chg'])==2 and sum(1 for c in after if c['del'])==1 and [c for c in after if c['p']=='Nashik_Crop'][0]['cls']=='dry', after)
    check('banner hidden after re-apply', not pg.is_visible('#restore-banner'))
    # fresh page, ZIP only, then import the reviewed file
    pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(1000)
    pg.set_input_files('#file-in', [FV]); pg.wait_for_timeout(2000)
    pg.click('.tabbtn[data-tab=review]'); pg.wait_for_timeout(500)
    pg.set_input_files('#an-file-in', saved_path); pg.wait_for_timeout(800)
    imp = pg.evaluate("({n:captures.length, chg:captures.filter(c=>isChanged(c)).length, noimg:captures.filter(c=>!c.imgUrl).length})")
    check('import reviewed file: 4 matched + 1 added w/o photo', imp['n']==5 and imp['noimg']==1 and imp['chg']==2, imp)
    # mobile layout
    m = b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2, is_mobile=True, has_touch=True)
    mp = m.new_page(); mp.on('pageerror', lambda e: errors.append('mobile: '+str(e)))
    mp.goto(BASE+'/explorer.html'); mp.wait_for_timeout(800)
    mp.screenshot(path=OUT+'/x06_m_empty.png')
    mp.set_input_files('#file-in', [FV, CV]); mp.wait_for_timeout(2500)
    mp.screenshot(path=OUT+'/x07_m_map.png')
    mp.click('#toggle-panel-btn'); mp.wait_for_timeout(500)
    mp.screenshot(path=OUT+'/x08_m_panel.png')
    mp.click('#toggle-panel-btn'); mp.wait_for_timeout(300)
    mp.evaluate("toggleTheme()"); mp.wait_for_timeout(300)
    mp.click('.tabbtn[data-tab=review]'); mp.wait_for_timeout(800)
    mp.screenshot(path=OUT+'/x09_m_review_light.png')
    b.close()

print('\npage errors:', errors or 'none')
non_tile = [u for u in failed_req if not any(h in u for h in ('basemaps.cartocdn.com','tile.openstreetmap.org','arcgisonline.com'))]
print('failed non-tile requests:', non_tile or 'none')
fails=[c for c in checks if not c[1]]
print(f'\n{len(checks)-len(fails)}/{len(checks)} checks passed')
sys.exit(1 if fails or errors or non_tile else 0)
