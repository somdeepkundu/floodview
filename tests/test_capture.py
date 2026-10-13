"""Headless end-to-end test of the FloodView capture app.
Fake camera + mocked GPS + synthetic orientation events (same event types a phone sends).
Usage: python3 test_capture.py <base_url> <outdir>"""
import sys, json, time, zipfile, io, os
from playwright.sync_api import sync_playwright

BASE, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
LAT, LON = 16.69120, 74.24390   # Kolhapur, Panchganga floodplain
errors, logs = [], []
checks = []
def check(name, cond, detail=''):
    checks.append((name, bool(cond), detail)); print(('PASS ' if cond else 'FAIL ') + name + (' — ' + str(detail) if detail != '' else ''))

ORI = """(()=>{ // phone held up, rear camera looking EAST, tilted 70° from straight down
  window.__ori = {alpha:270, beta:70, gamma:0};
  if(window.__oriTimer) clearInterval(window.__oriTimer);
  window.__oriTimer = setInterval(()=>{
    const o = window.__ori;
    window.dispatchEvent(new DeviceOrientationEvent('deviceorientationabsolute',{alpha:o.alpha,beta:o.beta,gamma:o.gamma,absolute:true}));
    window.dispatchEvent(new DeviceOrientationEvent('deviceorientation',{alpha:o.alpha,beta:o.beta,gamma:o.gamma,absolute:false}));
    window.dispatchEvent(new DeviceMotionEvent('devicemotion',{}));
  }, 60);
})()"""

with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--disable-gpu','--force-color-profile=srgb'])
    ctx = b.new_context(viewport={'width':360,'height':740}, device_scale_factor=2, is_mobile=True, has_touch=True,
                        geolocation={'latitude':LAT,'longitude':LON,'accuracy':6}, permissions=['geolocation','camera'],
                        accept_downloads=True, service_workers='allow')
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.on('console', lambda m: logs.append(m.type+': '+m.text) if m.type in ('error','warning') else None)
    pg.goto(BASE + '/index.html'); pg.wait_for_timeout(1500)
    pg.screenshot(path=OUT+'/01_start.png', full_page=False)
    pg.click('text=Grant Permissions')
    pg.evaluate(ORI)
    pg.wait_for_timeout(500)
    pg.screenshot(path=OUT+'/02_session.png')
    pg.fill('#pname', 'Kolhapur Test #1')
    pg.fill('#pnotes', 'Somdeep · smoke test')
    pg.click('text=Start Survey')
    pg.wait_for_timeout(2500)
    st = pg.evaluate("({name:S.proj.name, lat:S.lat, hdg:Math.round(S.heading), tilt:S.tilt, src:S.headingSrc, vw:document.getElementById('video').videoWidth})")
    check('session name sanitised', st['name']=='Kolhapur_Test__1', st['name'])
    check('GPS fix', abs((st['lat'] or 0)-LAT)<1e-6, st['lat'])
    check('heading east from orientation events', st['hdg']==90, st)
    check('tilt 70 from beta 70', st['tilt']==70, st['tilt'])
    check('camera stream live', st['vw']>0, st['vw'])
    aim = pg.evaluate("calcAim()")
    import math
    exp_d = 1.5*math.tan(math.radians(70))
    check('aim distance = H·tan(tilt)', abs(aim['dist']-exp_d)<1e-9, round(aim['dist'],3))
    check('aim point lies east of observer', aim['lon']>LON and abs(aim['lat']-LAT)<1e-6, (aim['lat'],aim['lon']))
    pg.screenshot(path=OUT+'/03_camera.png')

    # tags: depth knee, flow slow, trend rising, land road + cropland
    pg.click('#tc-depth'); pg.wait_for_timeout(300)
    pg.screenshot(path=OUT+'/04_sheet.png')
    pg.click('#ts-depth .opt:has-text("Knee")')
    pg.click('#ts-flow .opt:has-text("Slow")')
    pg.click('#ts-trend .opt:has-text("Rising")')
    pg.click('#ts-land .opt:has-text("Road")')
    pg.click('#ts-land .opt:has-text("Cropland")')
    pg.click('#ts-btns-live button:has-text("Done")')
    pg.wait_for_timeout(200)
    tags = pg.evaluate("S.tags")
    check('sticky tags set', tags['depth']=='knee' and tags['flow']=='slow' and tags['trend']=='rising' and tags['land']==['road','cropland'], tags)
    pg.click('#tc-edge'); pg.wait_for_timeout(200)
    check('edge mode on', pg.evaluate("S.tags.edge && document.body.classList.contains('edge-on')"))
    pg.screenshot(path=OUT+'/05_camera_tags_edge.png')

    pg.click('.cbtn.fl'); pg.wait_for_timeout(1200)
    # second edge point 25 m further north, looking east
    ctx.set_geolocation({'latitude':LAT+0.000225,'longitude':LON,'accuracy':6}); pg.wait_for_timeout(1500)
    pg.click('.cbtn.fl'); pg.wait_for_timeout(1200)
    pg.click('#tc-edge'); pg.wait_for_timeout(100)
    # dry point looking south-west, near horizon (tilt 88 -> no aim point, footprint clipped)
    pg.evaluate("window.__ori={alpha:135,beta:88,gamma:0}"); pg.wait_for_timeout(600)
    pg.click('.cbtn.dr'); pg.wait_for_timeout(1200)
    # waterlogged, phone pointing down at feet (tilt 20)
    pg.evaluate("window.__ori={alpha:0,beta:20,gamma:0}"); pg.wait_for_timeout(600)
    pg.click('.cbtn.wl'); pg.wait_for_timeout(1200)
    caps = pg.evaluate("S.caps.map(c=>({id:c.id,cls:c.cls,edge:c.edge,depth:c.depth,flow:c.flow,az:c.az,tilt:c.tilt,aim:c.aim,fp:c.fp}))")
    check('4 captures', len(caps)==4, len(caps))
    chrono = caps[::-1]
    check('classes in order', [c['cls'] for c in chrono]==['flooded','flooded','dry','waterlogged'], [c['cls'] for c in chrono])
    check('edge flags', [c['edge'] for c in chrono]==[True,True,False,False])
    check('dry forces no water/flow', chrono[2]['depth']=='none' and chrono[2]['flow'] is None, chrono[2])
    check('dry near-horizon: no aim point', chrono[2]['aim'] is None and chrono[2]['tilt']==88)
    check('dry heading SW (225)', chrono[2]['az']==225, chrono[2]['az'])
    check('waterlogged keeps sticky depth', chrono[3]['depth']=='knee', chrono[3]['depth'])
    nphotos = pg.evaluate("Promise.all(S.caps.map(c=>DB.getPhoto(c.id))).then(a=>a.filter(b=>b&&b.size>1000).length)")
    check('photos stored in IndexedDB', nphotos==4, nphotos)
    check('not in memory fallback', pg.evaluate("DB.mem")==False)

    pg.click('.tab[data-tab=map]'); pg.wait_for_timeout(1500)
    pg.screenshot(path=OUT+'/06_map.png')
    nlayers = pg.evaluate("({caps:S.capL.getLayers().length, fp:S.fpL.getLayers().length, edge:S.edgeL.getLayers().length})")
    check('map layers drawn', nlayers['edge']==1 and nlayers['fp']>=3, nlayers)
    pg.click('.tab[data-tab=data]'); pg.wait_for_timeout(800)
    pg.screenshot(path=OUT+'/07_data.png')
    pg.screenshot(path=OUT+'/07b_data_full.png', full_page=True)

    # edit the dry capture -> waterlogged + note
    dry_id = chrono[2]['id']
    pg.click(f'.ci:has-text("DRY") .chip:has-text("EDIT")'); pg.wait_for_timeout(300)
    pg.screenshot(path=OUT+'/08_edit_sheet.png')
    pg.click('#ts-cls .opt:has-text("Waterlogged")')
    pg.fill('#ts-note', 'ponding behind embankment')
    pg.click('#ts-btns-edit button:has-text("Save changes")'); pg.wait_for_timeout(500)
    ed = pg.evaluate(f"S.caps.find(c=>c.id==='{dry_id}')")
    check('edit saved', ed['cls']=='waterlogged' and ed['note']=='ponding behind embankment' and ed.get('edited'), (ed['cls'], ed['note']))

    # export ZIP
    with pg.expect_download() as dl:
        pg.click('text=📦 Export ZIP')
    d = dl.value; zpath = OUT+'/export.zip'; d.save_as(zpath)
    z = zipfile.ZipFile(zpath); names = z.namelist()
    check('zip has 4 images', len([n for n in names if n.startswith('images/') and n.endswith('.jpg')])==4, names)
    pts = json.loads(z.read([n for n in names if n.endswith('_captures_points.geojson')][0]))
    fps = json.loads(z.read([n for n in names if n.endswith('_captures_footprints.geojson')][0]))
    edge = json.loads(z.read([n for n in names if n.endswith('_water_edge.geojson')][0]))
    csv = z.read([n for n in names if n.endswith('.csv')][0]).decode()
    check('README present', 'README.txt' in names)
    pr = [f['properties'] for f in pts['features']]
    check('points: 4 features, chronological', [x['flood_class'] for x in pr]==['flooded','flooded','waterlogged','waterlogged'], [x['flood_class'] for x in pr])
    check('depth knee -> 45 cm body_scale', pr[0]['water_depth_class']=='knee' and pr[0]['water_depth_cm']==45 and pr[0]['water_depth_source']=='body_scale', pr[0])
    check('edited dry->waterlogged keeps depth none', pr[2]['water_depth_class']=='none' and pr[2]['water_depth_cm']==0, (pr[2]['water_depth_class'],pr[2]['water_depth_cm'],pr[2]['water_depth_source']))
    check('land cover string', pr[0]['flooded_land_cover']=='road;cropland', pr[0]['flooded_land_cover'])
    check('aim fields', pr[0]['aim_dist_m']==round(exp_d,2) and pr[0]['aim_lon']>LON, (pr[0]['aim_dist_m'], pr[0]['aim_uncertainty_m']))
    check('image names match files', all(('images/'+x['imgName']) in names for x in pr))
    check('fov_polygon member (CropView-compatible)', 'fov_polygon' in pts['features'][0])
    check('footprints: >=3 polygons', len(fps['features'])>=3, len(fps['features']))
    el = [f for f in edge['features'] if f['geometry']['type']=='LineString']
    ep = [f for f in edge['features'] if f['geometry']['type']=='Point']
    check('edge: 1 line through 2 crosshair points', len(el)==1 and len(ep)==2 and all(f['properties']['edge_from']=='crosshair' for f in ep), (len(el),len(ep)))
    line_len = None
    if el:
        (lo1,la1),(lo2,la2) = el[0]['geometry']['coordinates']
        line_len = math.hypot((la2-la1)*111320, (lo2-lo1)*111320*math.cos(math.radians(LAT)))
    obs = [(f['geometry']['coordinates'][1], f['geometry']['coordinates'][0]) for f in pts['features'] if f['properties']['water_edge']]
    exp_len = math.hypot((obs[1][0]-obs[0][0])*111320, (obs[1][1]-obs[0][1])*111320*math.cos(math.radians(LAT)))
    check('edge line length = distance between the two edge captures', line_len and exp_len>5 and abs(line_len-exp_len)<0.05, (round(line_len,2), round(exp_len,2)))
    aims=[(f['properties']['aim_lon'],f['properties']['aim_lat']) for f in pts['features'] if f['properties']['water_edge']]
    check('edge line runs through the crosshair points (±1e-7°)', all(abs(c[0]-a[0])<1e-7 and abs(c[1]-a[1])<1e-7 for c,a in zip(el[0]['geometry']['coordinates'],aims)))
    check('csv rows', len(csv.strip().split('\n'))==5)
    check('note in csv', 'ponding behind embankment' in csv)

    # reload -> resume -> data intact
    pg.evaluate("clearInterval(window.__oriTimer)")
    pg.reload(); pg.wait_for_timeout(1200)
    pg.click('text=Grant Permissions'); pg.evaluate(ORI); pg.wait_for_timeout(800)
    pg.screenshot(path=OUT+'/09_resume.png')
    check('resume list shows survey', pg.locator('.resume:has-text("Kolhapur_Test__1")').count()==1)
    pg.click('.resume:has-text("Kolhapur_Test__1")'); pg.wait_for_timeout(1500)
    after = pg.evaluate("({n:S.caps.length, camH:S.camH, notes:S.proj.notes, edited:S.caps.filter(c=>c.note).length})")
    check('resumed with 4 captures + edit', after['n']==4 and after['edited']==1 and after['notes']=='Somdeep · smoke test', after)
    nphotos = pg.evaluate("Promise.all(S.caps.map(c=>DB.getPhoto(c.id))).then(a=>a.filter(b=>b&&b.size>1000).length)")
    check('photos survive reload', nphotos==4, nphotos)
    swok = pg.evaluate("navigator.serviceWorker && navigator.serviceWorker.controller ? 'controlled' : (navigator.serviceWorker? 'registered?' : 'none')")
    print('service worker:', swok)
    b.close()

print('\npage errors:', errors or 'none')
print('console errors/warnings:', [l for l in logs if 'favicon' not in l][:15] or 'none')
fails = [c for c in checks if not c[1]]
print(f'\n{len(checks)-len(fails)}/{len(checks)} checks passed')
sys.exit(1 if fails or errors else 0)
