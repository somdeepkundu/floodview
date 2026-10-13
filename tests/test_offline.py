"""Offline check: open both pages once online, then cut the network and reload them."""
import sys
from playwright.sync_api import sync_playwright
BASE=sys.argv[1]; ok=True
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream'])
    ctx=b.new_context(service_workers='allow', geolocation={'latitude':16.7,'longitude':74.24}, permissions=['geolocation','camera'])
    pg=ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(BASE+'/index.html'); pg.wait_for_function("navigator.serviceWorker.controller!==null || document.getElementById('offline-state').classList.contains('ok')",timeout=15000)
    pg.reload(); pg.wait_for_timeout(1500)
    print('online state:', pg.inner_text('#offline-state'))
    ctx.set_offline(True)
    for page in ['index.html','explorer.html','']:
        pg.goto(BASE+'/'+page); pg.wait_for_timeout(1200)
        r=pg.evaluate("({title:document.title, leaflet:typeof L!=='undefined', jszip:typeof JSZip!=='undefined', font:document.fonts.check('12px Comfortaa')})")
        good=r['leaflet'] and r['jszip'] and 'FloodView' in r['title']
        ok&=good; print(('PASS ' if good else 'FAIL ')+'offline /'+page, r)
    # full capture offline
    pg.goto(BASE+'/index.html'); pg.wait_for_timeout(800)
    pg.click('text=Grant Permissions')
    pg.evaluate("setInterval(()=>window.dispatchEvent(new DeviceOrientationEvent('deviceorientationabsolute',{alpha:0,beta:60,gamma:0,absolute:true})),60)")
    pg.fill('#pname','Offline_Test'); pg.click('text=Start Survey'); pg.wait_for_timeout(2500)
    pg.click('.cbtn.fl'); pg.wait_for_timeout(1500)
    n=pg.evaluate("S.caps.length"); good=n==1; ok&=good; print(('PASS ' if good else 'FAIL ')+'capture while offline', n)
    with pg.expect_download() as d: pg.evaluate("doZIP(false)")
    good=d.value.suggested_filename.endswith('.zip'); ok&=good; print(('PASS ' if good else 'FAIL ')+'ZIP export while offline', d.value.suggested_filename)
    print('page errors:', errs or 'none'); ok&=not errs
    b.close()
sys.exit(0 if ok else 1)
