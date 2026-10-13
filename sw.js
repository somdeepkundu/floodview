/* FloodView service worker — lets the app open and work with no network.
   • App files (pages, libraries, font, icons): cached on install. Pages are
     fetched network-first (so updates arrive when online) and fall back to
     the cache; everything else is cache-first.
   • Map tiles: every tile you look at while online is kept (up to
     TILE_MAX), so a map you browsed before going out still shows offline.
   Bump VERSION whenever any cached file changes. */
const VERSION = 'floodview-1.1.1';
const TILE_CACHE = 'floodview-tiles';
const TILE_MAX = 3000;
const SHELL = [
  './', './index.html', './explorer.html', './manifest.json',
  './icons/icon.svg', './icons/icon-192.png', './icons/icon-512.png', './icons/icon-maskable-512.png',
  './vendor/leaflet/leaflet.js', './vendor/leaflet/leaflet.css',
  './vendor/leaflet/images/layers.png', './vendor/leaflet/images/layers-2x.png',
  './vendor/leaflet/images/marker-icon.png', './vendor/leaflet/images/marker-icon-2x.png', './vendor/leaflet/images/marker-shadow.png',
  './vendor/jszip.min.js',
  './vendor/fonts/comfortaa.css', './vendor/fonts/comfortaa-latin-wght-normal.woff2', './vendor/fonts/comfortaa-latin-ext-wght-normal.woff2'
];
const TILE_HOSTS = /(^|\.)tile\.openstreetmap\.org$|^server\.arcgisonline\.com$|(^|\.)basemaps\.cartocdn\.com$/;

self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== VERSION && k !== TILE_CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

function withTimeout(p, ms){ return Promise.race([p, new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), ms))]); }

async function networkFirst(req){
  const cache = await caches.open(VERSION);
  try{
    const res = await withTimeout(fetch(req), 4000);
    if(res && res.ok) cache.put(req, res.clone());
    return res;
  }catch(e){
    return (await cache.match(req, {ignoreSearch:true})) || (await cache.match('./index.html')) || Response.error();
  }
}
async function cacheFirst(req){
  const hit = await caches.match(req, {ignoreSearch:true});
  if(hit) return hit;
  const res = await fetch(req);
  if(res && res.ok){ const c = await caches.open(VERSION); c.put(req, res.clone()); }
  return res;
}
let trimming = false;
async function trimTiles(){
  if(trimming) return; trimming = true;
  try{
    const c = await caches.open(TILE_CACHE); const keys = await c.keys();
    for(let i = 0; i < keys.length - TILE_MAX; i++) await c.delete(keys[i]);   // oldest first
  }finally{ trimming = false; }
}
async function tile(req){
  const c = await caches.open(TILE_CACHE);
  const hit = await c.match(req);
  if(hit) return hit;
  try{
    const res = await fetch(req);
    if(res && (res.ok || res.type === 'opaque')){ c.put(req, res.clone()).then(trimTiles); }
    return res;
  }catch(e){ return Response.error(); }
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if(req.method !== 'GET') return;
  const url = new URL(req.url);
  if(TILE_HOSTS.test(url.hostname)){ e.respondWith(tile(req)); return; }
  if(url.origin !== self.location.origin) return;
  if(req.mode === 'navigate' || url.pathname.endsWith('.html') || url.pathname.endsWith('/')) e.respondWith(networkFirst(req));
  else e.respondWith(cacheFirst(req));
});
