/*
 * CowAgent console service worker.
 *
 * Only the static app shell is cached. Every live channel — the SSE reply
 * stream /stream, the /poll fallback, message/upload endpoints and the whole
 * /api surface — is explicitly passed straight through to the network. Buffering
 * any of those through the Cache API would stall streaming replies or serve
 * stale conversation state.
 */
const CACHE = 'cowagent-shell-v3';

// Precached so the standalone window still paints when the network is gone.
const SHELL_URLS = [
  '/',
  '/manifest.webmanifest',
  '/assets/icons/icon-192.png',
  '/assets/icons/icon-512.png',
  '/assets/icons/icon-maskable-512.png',
  '/assets/icons/apple-touch-icon.png',
];
const SHELL_FALLBACK = '/';

// Static, content-addressed (via ?v=) assets: safe to cache-first.
const STATIC_PREFIX = '/assets/';

// Live / stateful endpoints: never intercept, never cache.
const BYPASS_PREFIXES = [
  '/stream',
  '/poll',
  '/message',
  '/cancel',
  '/upload',
  '/uploads/',
  '/config',
  '/auth/',
  '/v1/',
  '/preview/',
  '/mcp/',
  '/api/',
];

// At most this many ?v= revisions are kept per asset path so the console's
// cache-busting query does not grow the cache without bound.
const MAX_VERSIONS_PER_ASSET = 2;

self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    await cache.addAll(SHELL_URLS);
    // Intentionally NOT calling skipWaiting(): a new worker waits until the
    // page accepts it, so an update never swaps assets out from under a user
    // mid-conversation. The page posts SKIP_WAITING when they click update.
  })());
});

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key)));
    await self.clients.claim();
  })());
});

function isBypassed(url) {
  return BYPASS_PREFIXES.some(
    (prefix) => url.pathname === prefix || url.pathname.startsWith(prefix),
  );
}

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  if (isBypassed(url)) return;

  // Navigations: network-first so a fresh build always wins, cached shell as
  // the offline fallback.
  if (request.mode === 'navigate') {
    event.respondWith((async () => {
      try {
        const fresh = await fetch(request);
        const cache = await caches.open(CACHE);
        cache.put(SHELL_FALLBACK, fresh.clone());
        return fresh;
      } catch (err) {
        const cached = await caches.match(SHELL_FALLBACK);
        return cached || Response.error();
      }
    })());
    return;
  }

  if (url.pathname.startsWith(STATIC_PREFIX)) {
    event.respondWith((async () => {
      const cached = await caches.match(request);
      if (cached) return cached;
      try {
        const fresh = await fetch(request);
        if (fresh && fresh.ok) {
          const cache = await caches.open(CACHE);
          await cache.put(request, fresh.clone());
          await trimVersions(cache, url.pathname);
        }
        return fresh;
      } catch (err) {
        return Response.error();
      }
    })());
  }
});

async function trimVersions(cache, pathname) {
  try {
    const keys = await cache.keys();
    const samePath = keys.filter((key) => new URL(key.url).pathname === pathname);
    if (samePath.length <= MAX_VERSIONS_PER_ASSET) return;
    await Promise.all(
      samePath.slice(0, samePath.length - MAX_VERSIONS_PER_ASSET).map((key) => cache.delete(key)),
    );
  } catch (err) {
    // Best-effort housekeeping; never let it break a fetch.
  }
}
